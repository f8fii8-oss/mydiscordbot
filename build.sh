#!/usr/bin/env bash
set -o errexit

apt-get update
apt-get install -y ffmpeg libopus0 opus-tools
pip install -r requirements.txt
