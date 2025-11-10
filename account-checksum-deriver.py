# pip3 install eth-keys eth-utils --break-system-packages  # noqa: D100
from eth_keys import keys  # type: ignore
from eth_utils import is_hex_address, to_checksum_address


def hex_to_bytes(s: str) -> bytes:  # noqa: D103
    s = s[2:] if s[:2].lower() == "0x" else s
    if len(s) % 2:
        s = "0" + s
    return bytes.fromhex(s)


def privkey_to_checksum_addr(*, privkey_hex: str) -> None:  # noqa: D103
    # convert hex to bytes
    privkey_bytes = hex_to_bytes(privkey_hex)

     # derive pubkey
    pk = keys.PrivateKey(privkey_bytes)

    # derive address
    addr = pk.public_key.to_checksum_address()
    print("Checksum address:", addr)


def addr_to_checksum_addr(*, addr: str) -> None:  # noqa: D103
    # force lowercase
    addr = addr.lower()

    # add 0x if necessary
    s = addr if addr.startswith("0x") else "0x" + addr

    if not is_hex_address(s):
        raise ValueError(f"Invalid hex address: {addr!r}")

    print("Checksum address:", to_checksum_address(s))


def main():  # noqa: D103
    # EXAMPLE 1: You have the private key and want to derive checksum addr
    privkey_hex = "0xfb1178767d9b9cc157a7a442e517d0dfddabc4d32929ffc83c1f40fc796a65c4"  # noqa: E501
    privkey_to_checksum_addr(privkey_hex=privkey_hex)

    # EXAMPLE 2: You have lowercase addr and want to derive checksum addr
    addr = "0xde5b20df5c96a2b20bc840d9a2c9230681eddcaf"
    addr_to_checksum_addr(addr=addr)

main()
