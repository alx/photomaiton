# photomaiton

```bash
sudo apt install python3.10-venv
git clone git@github.com:alx/photomaiton.git
```

## base

### connect to base

### run camera code on base

```bash
cd photomaiton/base
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## remote

### test local

``` bash
cd photomaiton/remote
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover tests
```

### gpu deploy

Fasttrack:

``` bash
git clone https://github.com/alx/photomaiton.git
./photomaiton/remote/deploy/mastodon_bot.sh
```

Manual:

``` bash
sudo sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
sudo apt update
sudo apt install python3.10-venv libgl1 magic-wormhole -y

python3.10 -m venv .venv && source .venv/bin/activate
echo ". .venv/bin/activate" >> ~/.bashrc

git clone https://github.com/alx/photomaiton.git
cd photomaiton/remote/
pip install -r requirements_gpu.txt
mkdir checkpoints && wget -O ./checkpoints/inswapper_128.onnx https://huggingface.co/ashleykleynhans/inswapper/resolve/main/inswapper_128.onnx

tmux

echo "Send config.json using wormhole: wormhole send config.json"
```
