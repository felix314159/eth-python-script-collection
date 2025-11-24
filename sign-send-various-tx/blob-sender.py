import json
from getpass import getpass
from pathlib import Path
from pprint import pprint
from typing import Any

from eth_account import Account             # pip3 install eth-account --break-system-packages
from eth_utils import to_checksum_address   # pip3 install eth-utils --break-system-packages
from hexbytes import HexBytes               # pip3 install hexbytes --break-system-packages

MAINNET_CHAIN_ID = 1
SEPOLIA_CHAIN_ID = 11155111

# ------------- helpers ---------------------------------
def read_keystore_file(*, keystore_file_path: str) -> str:
    with open(keystore_file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

def gwei_float_to_wei_int(gwei: float) -> int:
    return int(gwei * (10**9))

# -------------------------------------------------------
def load_blob(*, filepath: str) -> Any:
    """
    Load an execution-specs blob from json file and return its raw data and its versioned hash. 

    Example 1: Osaka Blob
    {
        'cells':    [       '0x...', # 2048 bytes, 4096 hex chars (not counting '0x' prefix)
                            '0x...',
                             ..., # in total 128 elements in cells
                    ]
        'commitment':       '0x...' # 48 bytes
        'data':             '0x...' # 128 KB of data
        'fork':             'Osaka',
        'name':             'blob_420_cell_proofs_128.json',
        'proof':    [       '0x...', # 48 bytes, 96 hex chars (not counting '0x' prefix)
                            '0x...',
                            ..., # in total 128 elements in proof, one for each cell
                    ],
        'seed':             420,
        'timestamp':        0,
        'versioned_hash':   '0x...' # 32 bytes hash
    }
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        blob_json = json.load(f)
    #pprint(blob_json)

    cells: list[str] = blob_json["cells"]
    data_hex: str = blob_json["data"]
    versioned_hash: str = blob_json["versioned_hash"]
    
    # below exist but are not relevant for this script
    #
    # commitment: str = blob_json["commitment"]
    # proof: list[str] = blob_json["proof"]
    # fork = blob_json["fork"]
    # name = blob_json["name"]
    # seed = blob_json["seed"]
    # timestamp = blob_json["timestamp"]

    # santity check
    if data_hex.startswith("0x"):
        data_hex = data_hex[2:]
    assert len(data_hex) == 131072*2, f"Data should be 128KB, got {len(data_hex)/2} bytes"
    blob_bytes = HexBytes(data_hex)

    # only do below for osaka <=
    if cells is not None:
        # reconstruct data from cells (first half of full_extended_data should match data_hex (the other half is just 1D erasure encoding))
        full_extended_data = b"".join([HexBytes(cell) for cell in cells])    
        assert blob_bytes == full_extended_data[:len(full_extended_data)//2]

        print(f"Raw Data Size:      {len(data_hex) // 2} bytes (128 KB)")
        print(f"Extended Cell Size: {len(full_extended_data)} bytes (256 KB)")

    return blob_bytes, versioned_hash

def main():
    # load osaka blob from file
    blob_filenames = [
                        Path("prague") / "blob_1337_cell_proofs_0.json",
                        Path("prague") / "blob_1338_cell_proofs_0.json",
                        Path("osaka") / "blob_1339_cell_proofs_128.json",
                     ]

    # define tx details
    chain_id = SEPOLIA_CHAIN_ID
    nonce = 6
    from_addr = "0x<redacted>"

    gas = 21_000
    max_priority_fee_per_gas = 0.1  # gwei
    max_fee_per_gas = 1.2           # gwei
    max_fee_per_blob_gas = 30       # gwei

    versioned_hashes = []
    blob_list = []
    for blob_file in blob_filenames:
        # read blob
        blob_bytes, versioned_hash = load_blob(filepath=blob_file)

        blob_list.append(blob_bytes)
        versioned_hashes.append(versioned_hash)

    tx_dict = {
        "type": 3,  # EIP-4844 blob transaction
        "chainId": chain_id,
        "nonce": nonce,
        "from": to_checksum_address(from_addr),
        "to": to_checksum_address(from_addr), # just send it to urself, on mainnet some L2's put "FF000....00<decimal-chainid>" as address
        "value": 0,
        "gas": gas,
        "maxPriorityFeePerGas": gwei_float_to_wei_int(max_priority_fee_per_gas),
        "maxFeePerGas": gwei_float_to_wei_int(max_fee_per_gas),
        "maxFeePerBlobGas": gwei_float_to_wei_int(max_fee_per_blob_gas),
        "data": "0x",
        "accessList": [],
        "blobVersionedHashes": versioned_hashes
    }
    pprint(tx_dict)

    # ------------------ sign ----------------------
    keystore_name = "UTC--<redacted>"
    keystore_file: str = read_keystore_file(keystore_file_path=keystore_name)
    pw: str = getpass("Enter Keystore Password: ")
    priv_key = Account.decrypt(keystore_file, pw) # wrong pw throws "ValueError: MAC mismatch"
    private_key_hex = priv_key.hex()
 
    signed_tx_obj = Account.sign_transaction(
        tx_dict, 
        private_key_hex,
        blobs=blob_list
    )
    signed_raw_tx_hex = "0x" + signed_tx_obj.raw_transaction.hex()
    Path("signed_raw_tx.txt").write_text(signed_raw_tx_hex) # overwrites existing
    print(f"exported raw tx, you can send this now via eth_sendRawTransaction")


if __name__ == "__main__":
    main()
# script assumes to be in same folder as keystore file

# Generate a blob in execution-specs:
#   from execution_testing.test_types.blob_types import *
#   from execution_testing.forks import Osaka, Prague
#   a = Blob.from_fork(fork=Osaka, seed=420)
#   b = Blob.from_fork(fork=Prague, seed=666)
#   -> ~/.cache/ethereum-execution-spec-tests/cached_blobs/
