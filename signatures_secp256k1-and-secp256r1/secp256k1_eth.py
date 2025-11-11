import json  # noqa: D100
from pprint import pprint

import requests
from cryptography.hazmat.primitives.asymmetric import ec
from eth_keys import keys  # type: ignore
from eth_keys.backends import CoinCurveECCBackend  # type: ignore
from eth_utils import keccak, to_checksum_address

RPC_URL = "http://127.0.0.1:8545"

ECRECOVER_PRECOMPILE = "0x0000000000000000000000000000000000000001"  # ecrec
N = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)
N_OVER_2 = N // 2

def eth_prefix_keccak(msg_bytes: bytes) -> bytes:  # noqa: D103
    prefix = b"\x19Ethereum Signed Message:\n" + str(len(msg_bytes)).encode()
    return keccak(prefix + msg_bytes)

def ensure_low_s(sig):  # noqa: D103
    assert 1 <= sig.s <= N_OVER_2, f"s not low-S: {hex(sig.s)}"

def ensure_deterministic(priv, digest32: bytes):  # noqa: D103
    s1 = priv.sign_msg_hash(digest32)
    s2 = priv.sign_msg_hash(digest32)
    assert (s1.r, s1.s) == (s2.r, s2.s), "non-deterministic signature"
    return s1

def sig_hex_caststyle(sig):  # noqa: D103
    v_eth = sig.v + 27
    return (
        "0x"
        + sig.r.to_bytes(32, "big").hex()
        + sig.s.to_bytes(32, "big").hex()
        + v_eth.to_bytes(1, "big").hex()
    )

def i2b32(i: int) -> bytes:  # noqa: D103
    return i.to_bytes(32, "big", signed=False)

def b2hex(b: bytes) -> str:  # noqa: D103
    return "0x" + b.hex()

def pubkey_xy_from_cryptography_pub(pubkey: ec.EllipticCurvePublicKey) -> tuple[bytes, bytes]:  # noqa: D103, E501
    nums = pubkey.public_numbers()
    return i2b32(nums.x), i2b32(nums.y)

def main():  # noqa: D103
    perform_rpc_call = True

    # 1) Generate a secp256k1 keypair
    priv = ec.generate_private_key(ec.SECP256K1())
    qx, qy = pubkey_xy_from_cryptography_pub(priv.public_key())
    d_int = priv.private_numbers().private_value
    d_bytes = i2b32(d_int)
    backend = CoinCurveECCBackend()
    eth_priv = keys.PrivateKey(d_bytes, backend=backend)
    eth_pub = eth_priv.public_key
    signer_addr = eth_pub.to_checksum_address()
    print(f"Private Key: {eth_priv}\nSigner ETH Address: {signer_addr}")

    # 2) Define message and calculates eth-specific sig (put ethereum msg prefix etc and use keccak256 as hash function)  # noqa: E501
    msg = b"hello world"
    print("Message:", msg.decode())

    h_keccak = eth_prefix_keccak(msg)
    sig_keccak = ensure_deterministic(eth_priv, h_keccak)
    ensure_low_s(sig_keccak)
    print("foundry cast sig:", sig_hex_caststyle(sig_keccak))

    # 3) Sign the hash with ECDSA-secp256k1 and obtain (r, s, v)
    r = sig_keccak.r
    s = sig_keccak.s
    v = sig_keccak.v

    r_b = i2b32(r)
    s_b = i2b32(s)
    v_b = i2b32(v + 27)

    # Show fields
    print("h(ash) =", b2hex(h_keccak))
    print("r =", b2hex(r_b))
    print("s =", b2hex(s_b))
    print("v_b =", int.from_bytes(v_b, byteorder="big"))
    print("qx =", b2hex(qx))
    print("qy =", b2hex(qy))
    print("sig =", sig_keccak)

    # 4) Sanity checks
    #       Local verification: recover pubkey from (h, v, r, s) and compare to ours  # noqa: E501
    recovered_pub = sig_keccak.recover_public_key_from_msg_hash(h_keccak)
    assert recovered_pub == eth_pub, "local ECDSA recovery failed"

    p = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F", 16)  # noqa: E501
    a = 0
    b = 7
    n = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141", 16)  # noqa: E501

    ri = int.from_bytes(r_b, "big")
    si = int.from_bytes(s_b, "big")
    qxi = int.from_bytes(qx, "big")
    qyi = int.from_bytes(qy, "big")

    assert 1 <= ri < n and 1 <= si < n, "r or s out of range"
    assert 0 <= qxi < p and 0 <= qyi < p, "qx or qy out of range"
    assert pow(qyi, 2, p) == (pow(qxi, 3, p) + a * qxi + b) % p, "public key not on curve"  # noqa: E501
    assert len(h_keccak) == 32
    assert len(v_b) == 32
    assert len(r_b) == 32
    assert len(s_b) == 32

    # --------------- Get local RPC response from node ------------------------

    # 5) Construct calldata
    calldata = h_keccak + v_b + r_b + s_b
    calldata_hex = "0x" + calldata.hex()

    # 6) eth_call to the precompile of a locally running exec client
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{
            "to": ECRECOVER_PRECOMPILE,
            "data": calldata_hex,
            #"data": calldata_hex[:-1] + chr(ord(calldata_hex[-1]) ^ 1), # change last char of sig to invalidate it  # noqa: E501
            "gas": hex(100000)
        }, "latest"]
    }

    json_body = json.dumps(payload, separators=(",", ":"))
    curl_cmd = f"curl -fsS -X POST -H 'Content-Type: application/json' --data '{json_body}' {RPC_URL} && echo"  # noqa: E501
    print("\nRun this in bash to reproduce the request:")
    print(curl_cmd, "\n")

    if perform_rpc_call:
        resp = requests.post(
            RPC_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        ).json()

        if "error" in resp:
            raise RuntimeError(resp["error"])

        print("Response:")
        pprint(resp)
        print()

        # 7) Parse the 32-byte return: rightmost 20 bytes are the address (left-padded with zeros).  # noqa: E501
        out = bytes.fromhex(resp.get("result")[2:]) if resp.get("result") and resp.get("result").startswith("0x") else b""  # noqa: E501
        if len(out) != 32:
            raise RuntimeError(f"unexpected return length ({len(out)}): {out}")

        recovered_addr_bytes = out[-20:]
        recovered_addr = to_checksum_address("0x" + recovered_addr_bytes.hex())
        assert recovered_addr == signer_addr, f"signature is invalid: recovered address {recovered_addr} but expected address {signer_addr}"  # noqa: E501

        print("signature is valid!")

if __name__ == "__main__":
    main()

"""
Independently verify that signatures this script produces are correct using foundry cast:

    cast wallet sign <message text> --private-key <hex_private_key>

e.g.

    cast wallet sign "hello world" --private-key 0x2d2a6e78ddac7528f7580406c6384779e9bd9abd6300f2c7b75d8eb2d0b9206d

->  0xcfdf1db02499997418c7c83388589eaf32cc3668eb9894a8cb8fd3f0f6337fe811f16f5c94a871f651d002568d4f46236b7d0e0eaddea3bbf95f829a1ce3a8b71c
"""  # noqa: E501
