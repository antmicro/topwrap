#!/usr/bin/env sh

set -e

cd $(dirname $0)/../../docs

pip3 install -r requirements.txt

cd build/latex
LATEXMKOPTS='-interaction=nonstopmode' make
cp *.pdf ../html/
