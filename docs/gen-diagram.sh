#!/bin/sh

set -ex

mkdir -p docs/build/
pyreverse --output-directory docs/build/ --output mmd topwrap.model --no-standalone

(
    echo "
%%{init: {'theme': 'neutral'}}%%
";
    cat docs/build/classes.mmd;
) > docs/source/img/ir_classes.mmd
