#!/bin/bash
# This script is meant to be run on a fresh Ubuntu 20.04 install
# It will install all the dependencies needed to run photomaiton

sudo sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
sudo apt update
sudo apt install tmux python3.10-venv libgl1 magic-wormhole -y

python3.10 -m venv .venv && source .venv/bin/activate
echo ". .venv/bin/activate" >> ~/.bashrc

cd $HOME/photomaiton/remote/
pip install -r requirements_gpu.txt
mkdir checkpoints && wget -O ./checkpoints/inswapper_128.onnx https://huggingface.co/ashleykleynhans/inswapper/resolve/main/inswapper_128.onnx

echo "Send config.json using wormhole: wormhole send config.json"
