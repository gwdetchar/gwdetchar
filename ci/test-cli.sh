#!/bin/bash
#
# Travis CI test runner: test --help for all command-line interfaces
# Author: Duncan Macleod <duncan.macleod@ligo.org> (2019)
#         Alex Urban <alexander.urban@ligo.org> (2019-2020)

FAILED=()

echo "---- Testing python -m modules ----"

# loop over python modules
modules=(
    gwdetchar.conlog
    gwdetchar.lasso
    gwdetchar.lasso.old
    gwdetchar.mct
    gwdetchar.nagios
    gwdetchar.omega
    gwdetchar.omega.batch
    gwdetchar.overflow
    gwdetchar.saturation
    gwdetchar.scattering
    gwdetchar.scattering.simple
)
for MODULE in "${modules[@]}"; do
    # execute --help with coverage
    echo ""
    echo "$ python -m ${MODULE} --help"
    python -m coverage run --append --source=gwdetchar -m ${MODULE} --help;
    if [ "$?" -ne 0 ]; then                                                     
        FAILED+=("${MODULE}")                                                  
    fi
done

if [ ${#FAILED[@]} -ne 0 ]; then
    echo "---- The following modules failed: ----"
    for failure in "${FAILED[@]}"; do
        echo ${failure}
    done
    exit 1
fi
echo ""
echo "---- All modules passed ----"
