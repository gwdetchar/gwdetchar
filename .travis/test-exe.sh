#!/bin/bash

exe_=$1
shift
coverage run --append --source=gwdetchar --omit="gwdetchar/_version.py" `which ${exe_}` $@
