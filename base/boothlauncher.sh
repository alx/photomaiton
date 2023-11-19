#!/bin/sh
#Launch photo booth python script at startup

cd /
cd home/minutepapillons/photomaiton/base
#sudo rm -rf captures
#sudo python -m pip uninstall mastodon-py
#sudo python -m pip install mastodon-py
sudo python3 main.py
#sudo python main.py "/media/minutepapillons/BOOTH"
cd /