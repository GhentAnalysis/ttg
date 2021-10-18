#!/bin/env bash

nmax=-1

xml="test.xml"

python makeTree.py \
--output=output.root \
--xml=${xml} \
--nmax=${nmax} \
--sample=output \
--tag=output
