import os
import pathlib
import tempfile

import jinja2
import modal
from jinja2 import select_autoescape
from modal import Image, Stub

cicd_path = pathlib.Path(__file__).parent.resolve()

template_loader = jinja2.FileSystemLoader(searchpath=cicd_path)
template_env = jinja2.Environment(
    loader=template_loader, autoescape=select_autoescape()
)
df_template = template_env.get_template("Dockerfile.jinja")

df_args = {
    "AXOLOTL_EXTRAS": os.environ.get("AXOLOTL_EXTRAS"),
    "PYTORCH_VERSION": os.environ.get("PYTORCH_VERSION", "2.0.1"),
    "BASE_TAG": os.environ.get("BASE_TAG", "main-base-py3.10-cu118-2.0.1"),
    "CUDA": os.environ.get("CUDA", "118"),
    "GITHUB_REF": os.environ.get("GITHUB_REF", "ref/heads/main"),
    "GITHUB_SHA": os.environ.get("GITHUB_SHA"),
}

dockerfile_contents = df_template.render(**df_args)

temp_dir = tempfile.mkdtemp()
with open(pathlib.Path(temp_dir) / "Dockerfile", "w") as f:
    f.write(dockerfile_contents)

DOCKER_ENV = {
    "PYTORCH_VERSION": os.environ.get("PYTORCH_VERSION"),
    "BASE_TAG": os.environ.get("BASE_TAG"),
    "CUDA": os.environ.get("CUDA"),
    # "GITHUB_REF": os.environ.get("GITHUB_REF", "refs/head/main"),
    "GITHUB_REF": os.environ.get("GITHUB_REF", "refs/heads/modal-ci"),
}

cicd_image = Image.from_dockerfile(
    pathlib.Path(temp_dir) / "Dockerfile",
    force_build=True,
    gpu="A10G",
).env(DOCKER_ENV)

stub = Stub("Axolotl CI/CD", secrets=[])


N_GPUS = int(os.environ.get("N_GPUS", 2))
GPU_CONFIG = modal.gpu.A10G(count=N_GPUS)


def run_cmd(cmd: str, run_folder: str):
    import subprocess  # nosec

    # Propagate errors from subprocess.
    if exit_code := subprocess.call(cmd.split(), cwd=run_folder):  # nosec
        exit(exit_code)


@stub.function(
    image=cicd_image,
    gpu=GPU_CONFIG,
    timeout=60 * 30,
)
def cicd_pytest():
    CMD = "pytest /workspace/axolotl/tests/e2e/patched/"
    run_cmd(CMD, "/workspace/axolotl")


@stub.local_entrypoint()
def main():
    cicd_pytest.remote()
