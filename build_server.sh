#!/bin/bash

git submodule update --init

pushd kenning-pipeline-manager
pip install -r requirements.txt
./build server-app
popd
