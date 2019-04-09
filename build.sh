#!/usr/bin/env bash

set -e

pip install -r requirements_dev.txt
python setup.py sdist bdist_wheel
