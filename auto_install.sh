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

    # Immediately export Miniconda path for the current script execution
    export PATH="$HOME/miniconda3/bin:$PATH"

    # Append the export command to ~/.bashrc for future sessions
    echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc

    # Initialize Conda for bash shell
    echo "Initializing Conda..."
    conda init bash
fi

# No need to source ~/.bashrc here since we've already manually updated PATH

# Create a new Conda environment with Python 3.10
echo "Creating a new Conda environment 'axolotl' with Python 3.10..."
conda create -n axolotl python=3.10 --yes

# Initialize Conda again to ensure the environment is properly set up
conda init bash

# Activate the newly created Conda environment
echo "Activating the 'axolotl' environment..."
source activate axolotl || source $HOME/miniconda3/bin/activate axolotl

# Install CUDA and PyTorch with dependencies
echo "Installing CUDA and PyTorch with dependencies..."
conda install -y -c "nvidia/label/cuda-12.1.1" cuda --yes
conda install pytorch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 pytorch-cuda=12.1 -c pytorch -c nvidia --yes

# Change directory to axolotl
cd axolotl

# Install additional Python packages
echo "Installing additional Python packages..."
pip3 install packaging
pip3 install -e '.[flash-attn,deepspeed]'

pip3 uninstall deepspeed -y
pip3 install deepspeed==0.13.1

echo "Setup completed successfully."
