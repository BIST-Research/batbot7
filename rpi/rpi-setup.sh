#!/bin/bash

# update and upgrade
sudo apt update
sudo apt upgrade -y

# give add user to dialout and sftp and batrun groups
# requires reboot
sudo mkdir /home/batrun
sudo groupadd sftp
sudo groupadd batrun
sudo useradd -m sftp_batbot -g sftp
sudo passwd sftp_batbot

sudo chmod 770 /home/batrun
sudo chmod +s /home/batrun

sudo usermod -aG sftp sftp_batbot
sudo usermod -aG dialout batbot
sudo usermod -aG batrun sftp_batbot
sudo usermod -aG batrun batbot

# sudo reboot

# install some packages
sudo apt install -y htop neofetch curl
sudo apt install -y python3-dev python3-full

# create python virtual environment
python3 -m venv /home/batbot7/pyvenv
source /home/batbot7/pyvenv/bin/activate

# create alias to venv
alias py3=/home/batbot7/pyvenv/bin/python3

# install required python modules
py3 -m pip install matplotlib scipy numpy pyyaml pyserial
py3 -m pip install pygnssutils gpxpy

# setup sftp
sudo echo "Match group sftp" >> /etc/ssh/sshd_config
sudo echo "ChrootDirectory /home" >> /etc/ssh/sshd_config
sudo echo "X11Forwarding yes" >> /etc/ssh/sshd_config
sudo echo "AllowTcpForwarding no" >> /etc/ssh/sshd_config
sudo echo "ForceCommand internal-sftp" >> /etc/ssh/sshd_config
sudo systemctl restart ssh

