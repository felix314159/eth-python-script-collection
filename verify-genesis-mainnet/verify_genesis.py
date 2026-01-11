import json
from pathlib import Path

# prereq: pip install rlp trie eth-utils eth-hash[pycryptodome] --break-system-packages
import rlp
from rlp.sedes import Binary, big_endian_int
from trie import HexaryTrie
from eth_utils import keccak, to_canonical_address


# goal of the script is to verify the correctness of this value
MAINNET_GENESIS_HASH = bytes.fromhex(
    "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
)

# Hash of rlp("")
EMPTY_TRIE_ROOT = keccak(rlp.encode(b""))

# Hash of rlp([])
EMPTY_UNCLES_HASH = keccak(rlp.encode([]))

# keccak256(b"")
EMPTY_CODE_HASH = keccak(text="")

EMPTY_LOGS_BLOOM = b"\x00" * (2048 / 8)  # 2048-bit bloom filter
ZERO_HASH32 = b"\x00" * 32


def parse_int(v) -> int:
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.strip()
        if v.startswith(("0x", "0X")):
            return int(v, 16)
        return int(v)
    raise TypeError(f"Unsupported int value: {v!r}")


def parse_hex_bytes(v, *, length: int | None = None) -> bytes:
    if isinstance(v, str):
        h = v[2:] if v.startswith(("0x", "0X")) else v
        b = bytes.fromhex(h) if h else b""
    elif isinstance(v, (bytes, bytearray)):
        b = bytes(v)
    else:
        raise TypeError(f"Unsupported hex value: {v!r}")

    if length is not None:
        if len(b) > length:
            raise ValueError(f"value too long: {len(b)} > {length}")
        if len(b) < length:
            b = b.rjust(length, b"\x00")
    return b


class Account(rlp.Serializable):
    """
    RLP account as defined in the Yellow Paper:
    [ nonce, balance, storageRoot, codeHash ]
    """

    fields = [
        ("nonce", big_endian_int),
        ("balance", big_endian_int),
        ("storage_root", Binary.fixed_length(32)),
        ("code_hash", Binary.fixed_length(32)),
    ]


class Header(rlp.Serializable):
    """
    Block header RLP:
    [
      parentHash, ommersHash, beneficiary, stateRoot,
      transactionsRoot, receiptsRoot, logsBloom,
      difficulty, number, gasLimit, gasUsed,
      timestamp, extraData, mixHash, nonce
    ]
    """

    fields = [
        ("parent_hash", Binary.fixed_length(32)),
        ("uncles_hash", Binary.fixed_length(32)),
        ("coinbase", Binary.fixed_length(20)),
        ("state_root", Binary.fixed_length(32)),
        ("transactions_root", Binary.fixed_length(32)),
        ("receipts_root", Binary.fixed_length(32)),
        ("logs_bloom", Binary.fixed_length(256)),
        ("difficulty", big_endian_int),
        ("number", big_endian_int),
        ("gas_limit", big_endian_int),
        ("gas_used", big_endian_int),
        ("timestamp", big_endian_int),
        ("extra_data", Binary()),
        ("mix_hash", Binary.fixed_length(32)),
        ("nonce", Binary.fixed_length(8)),
    ]


def compute_state_root(alloc: dict) -> bytes:
    """
    Build the state trie from the 'alloc' section of a genesis and
    return its root hash.
    """
    trie = HexaryTrie(db={})

    for addr_hex, entry in alloc.items():
        if isinstance(entry, (int, str)):
            balance = parse_int(entry)
        else:
            balance = parse_int(entry.get("balance", 0))

        addr = to_canonical_address(addr_hex)
        trie_key = keccak(addr)

        account = Account(
            nonce=0,
            balance=balance,
            storage_root=EMPTY_TRIE_ROOT,
            code_hash=EMPTY_CODE_HASH,
        )
        trie[trie_key] = rlp.encode(account)

    return trie.root_hash



def make_genesis_header(genesis_dict: dict, state_root: bytes) -> Header:
    """
    Construct the block 0 header from a go-ethereum-style genesis dict
    (fields like nonce, timestamp, gasLimit, difficulty, mixHash, coinbase, etc.)
    plus the computed state_root.
    """
    parent_hash = ZERO_HASH32
    uncles_hash = EMPTY_UNCLES_HASH

    coinbase = to_canonical_address(
        genesis_dict.get(
            "coinbase",
            "0x0000000000000000000000000000000000000000",
        )
    )

    difficulty = parse_int(genesis_dict["difficulty"])
    gas_limit = parse_int(genesis_dict["gasLimit"])
    timestamp = parse_int(genesis_dict["timestamp"])

    number = 0
    gas_used = 0

    extra_data = parse_hex_bytes(genesis_dict.get("extraData", "0x"))
    mix_hash = parse_hex_bytes(
        genesis_dict.get("mixHash", "0x" + "00" * 32),
        length=32,
    )
    nonce = parse_hex_bytes(genesis_dict["nonce"], length=8)

    tx_root = EMPTY_TRIE_ROOT
    receipts_root = EMPTY_TRIE_ROOT
    logs_bloom = EMPTY_LOGS_BLOOM

    return Header(
        parent_hash=parent_hash,
        uncles_hash=uncles_hash,
        coinbase=coinbase,
        state_root=state_root,
        transactions_root=tx_root,
        receipts_root=receipts_root,
        logs_bloom=logs_bloom,
        difficulty=difficulty,
        number=number,
        gas_limit=gas_limit,
        gas_used=gas_used,
        timestamp=timestamp,
        extra_data=extra_data,
        mix_hash=mix_hash,
        nonce=nonce,
    )


def compute_genesis_hash_from_file(path: str | Path) -> bytes:
    """
    Load a genesis JSON with 'alloc' and typical go-ethereum-style
    header fields, recompute the genesis header hash, and return it.
    """
    path = Path(path)
    data = json.loads(path.read_text())
    alloc = data["alloc"]

    state_root = compute_state_root(alloc)
    header = make_genesis_header(data, state_root)
    encoded_header = rlp.encode(header)
    return keccak(encoded_header)


def verify_mainnet_genesis_from_file(path: str | Path) -> bool:
    h = compute_genesis_hash_from_file(path)
    if h != MAINNET_GENESIS_HASH:
        raise ValueError(
            f"Genesis mismatch:\n"
            f"  computed: 0x{h.hex()}\n"
            f"  expected: 0x{MAINNET_GENESIS_HASH.hex()}"
        )
    return True


if __name__ == "__main__":
    # ensure ./mainnet.json exists
    ok = verify_mainnet_genesis_from_file("mainnet.json")
    print("Genesis hash verified from alloc:", ok)
