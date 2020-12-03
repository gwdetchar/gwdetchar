#!/bin/bash
#
# Travis CI test runner: test --help for all command-line interfaces
# Author: Duncan Macleod <duncan.macleod@ligo.org> (2019)
#         Alex Urban <alexander.urban@ligo.org> (2019-2020)

FAILED=()

echo "---- Testing scripts in /bin/ ----"

# loop over all bin/ scripts
for EXE in bin/*; do
    # get file-name as PATH executable
    EXENAME=$(basename ${EXE})
    EXEPATH=$(which ${EXENAME})
    if [ "$?" -ne 0 ]; then
        FAILED+=(${EXENAME_})
        continue
    fi

    # execute --help with coverage
    echo ""
    echo "$ ${EXENAME} --help"
    python -m coverage run --append --source=gwdetchar ${EXEPATH} --help;
    if [ "$?" -ne 0 ]; then
        FAILED+=("${EXENAME}")
        continue
    fi
done

echo ""
echo ""
echo "---- Testing python -m modules ----"

# loop over python modules
modules=(
    gwdetchar.conlog
    gwdetchar.nagios
    gwdetchar.omega
    gwdetchar.omega.batch
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
    echo "---- The following scripts failed: ----"
    for failure in "${FAILED[@]}"; do
        echo ${failure}
    done
    exit 1
fi
echo "---- All scripts passed ----"
