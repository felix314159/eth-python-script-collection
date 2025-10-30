# eth-python-script-collection
I sometimes dump ethereum-related Python scripts here, use at own risk ;)

## Overview
* `complement-calc.py`: Calculates One's and Two's complement for various bit sizes, support hex and bin output.
* `contract_address_precalculator.py`: Pre-calculate the address of contracts before deploying them (do not use to brute-force first and last 4 hex digits collision of another contract plz)
* `badly-broken-string-finder/find-useless-strings.py`: In Python you can accidentally break a string across multiple lines and forgot to put into parenthesis. Then there won't be any error but the string literals will silently be dropped. Ruff can't detect this at all (B018 implementation not good enough), pylint W0104 can only catch certain scenarios (when you silently drop f-strings, but not when you silently drop normal string literals). This script catches all such cases as far as I know, it's quite important to check for this. Imagine you try to run sth on a folder but you split the path wrongly, and the actual relevant subfolder is silently dropped and now you touch files you never intended to touch.
* `eip-checker.py`: Takes EIP number as input and returns which fork this EIP was included in (if at all). Also retrieves all other EIPs that were in this fork.
* `find-duplicates.py`: Helper for finding duplicates (files, folders, classes, functions) in a large Python project.
* `line_length_checker.py`: Counts amount of violations of MAX_LENGTH_PER_LINE rules (e.g. pep8's antique 79 rule)
* `./mnemonic/mnemonic_deriver.py`: Generates ethereum accounts for testing purposes. Generates valid mnemonics, derives accounts, mines vanity addresses, little pyramids stuff like that 
