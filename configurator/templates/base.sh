#!/usr/bin/env bash
export LC_ALL=$LANG
apt-get update
apt-get install build-essential python-dev -y
pip install virtualenvwrapper
exit $?
