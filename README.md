# eth-python-script-collection
I sometimes dump ethereum-related Python scripts here, use at own risk ;)

## Overview
* `complement-calc.py`: Calculates One's and Two's complement for various bit sizes, support hex and bin output.
* `contract_address_precalculator.py`: Pre-calculate the address of contracts before deploying them (do not use to brute-force first and last 4 hex digits collision of another contract plz)
* `eip-checker.py`: Takes EIP number as input and returns which fork this EIP was included in (if at all). Also retrieves all other EIPs that were in this fork.
* `find-duplicates.py`: Helper for finding duplicates (files, folders, classes, functions) in a large Python project.
* `line_length_checker.py`: Counts amount of violations of MAX_LENGTH_PER_LINE rules (e.g. pep8's antique 79 rule)
* `mnemonic_deriver.py`: Generates ethereum accounts for testing purposes (do not use in production!). Also allows deriving key-address pairs from invalid mnemonics (but why should you)
