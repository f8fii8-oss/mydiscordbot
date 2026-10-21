#!/usr/bin/env bash
# Exit on error
set -o errexit

apt-get update && apt-get install -y ffmpeg
pip install -r requirements.txt
