#!/usr/bin/env sh

set -e

cd $(dirname $0)/../../docs

pip3 install --user -r requirements.txt

make html latex
