#!/bin/bash
#
# Travis CI test runner: test --help for all command-line executables
# Author: Duncan Macleod <duncan.macleod@ligo.org> (2019)

FAILED=()

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
    echo "${EXENAME} --help..."
    python -m coverage run --append --source=gwdetchar ${EXEPATH} --help;
    if [ "$?" -ne 0 ]; then
        FAILED+=("${EXENAME}")
        continue
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
