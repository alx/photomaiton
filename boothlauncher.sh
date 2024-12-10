#!/usr/bin/env bash
#Launch photo booth python script at startup

cd /
cd home/minutepapillons/photomaiton/base
#sudo rm -rf captures
source activatevenv.sh
python main.py
cd /
