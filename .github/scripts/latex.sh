#!/usr/bin/env sh

set -e

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
  python3-pip \
  python3-setuptools \
  python3-wheel

cd $(dirname $0)/../../docs

pip3 install --user -r requirements.txt

cd build/latex
LATEXMKOPTS='-interaction=nonstopmode' make
cp *.pdf ../html/
