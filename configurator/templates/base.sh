#!/usr/bin/env bash
export LC_ALL=$LANG
apt-get update
apt-get install build-essential python-dev -y
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
rm -f get-pip*
pip install virtualenvwrapper
exit $?
