"""
CLI to run training on a model
"""
from pathlib import Path

import fire
import transformers

from axolotl.cli import load_cfg, load_datasets, print_axolotl_text_art, check_accelerate_default_config
from axolotl.common.cli import TrainerCliArgs
from axolotl.train import train


def do_cli(config: Path = Path("examples/"), **kwargs):
    # pylint: disable=duplicate-code
    print_axolotl_text_art()
    check_accelerate_default_config()
    parsed_cfg = load_cfg(config, **kwargs)
    parser = transformers.HfArgumentParser((TrainerCliArgs))
    parsed_cli_args, _ = parser.parse_args_into_dataclasses(
        return_remaining_strings=True
    )

    dataset_meta = load_datasets(cfg=parsed_cfg, cli_args=parsed_cli_args)
    if parsed_cli_args.prepare_ds_only:
        return
    train(cfg=parsed_cfg, cli_args=parsed_cli_args, dataset_meta=dataset_meta)


fire.Fire(do_cli)
