#!/bin/bash

# Exit script if any command fails
set -e

if command -v conda &>/dev/null; then
    echo "Conda is already installed. Skipping Conda/Miniconda installation."
else
    # Download Miniconda installer
    echo "Downloading Miniconda installer..."
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O Miniconda3-latest-Linux-x86_64.sh

    # Install Miniconda silently
    echo "Installing Miniconda..."
    bash Miniconda3-latest-Linux-x86_64.sh -b

    # Export Miniconda path temporarily for the script
    export PATH="$HOME/miniconda3/bin:$PATH"

    # Initialize Conda for bash shell
    echo "Initializing Conda..."
    conda init bash

    # Refresh shell to apply conda init changes. Using source to avoid starting a new shell.
    source ~/.bashrc
fi

# Create a new Conda environment with Python 3.10
echo "Creating a new Conda environment 'axolotl' with Python 3.10..."
conda create -n axolotl python=3.10 --yes

# Initialize Conda again to ensure the environment is properly set up
conda init bash

# Activate the newly created Conda environment
echo "Activating the 'axolotl' environment..."
source activate axolotl

# Install CUDA and PyTorch with dependencies
echo "Installing CUDA and PyTorch with dependencies..."
conda install -y -c "nvidia/label/cuda-12.1.1" cuda --yes
conda install pytorch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 pytorch-cuda=12.1 -c pytorch -c nvidia --yes

# Assuming the script is run from the root of the cloned 'axolotl' repository, so no need to clone it again
# Install additional Python packages
echo "Installing additional Python packages..."
pip3 install packaging
pip3 install -e '.[flash-attn,deepspeed]'

# Append the environment activation command to the user's shell startup file
if [[ -f ~/.bashrc ]]; then
    echo "conda activate axolotl" >> ~/.bashrc
    echo "Conda 'axolotl' environment will be automatically activated in new bash sessions."
elif [[ -f ~/.zshrc ]]; then
    echo "conda activate axolotl" >> ~/.zshrc
    echo "Conda 'axolotl' environment will be automatically activated in new zsh sessions."
fi

echo "Setup completed successfully."
