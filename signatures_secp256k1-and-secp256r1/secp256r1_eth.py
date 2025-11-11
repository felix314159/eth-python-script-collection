import hashlib  # noqa: D100
import json

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    decode_dss_signature,
    encode_dss_signature,
)
from eth_keys import keys  # type: ignore
from eth_keys.backends import CoinCurveECCBackend  # type: ignore

RPC_URL = "http://127.0.0.1:8545"

# EIP 7951 constants
P256_PRECOMPILE = "0x0000000000000000000000000000000000000100"
p = int("ffffffff00000001000000000000000000000000ffffffffffffffffffffffff", 16)  # Base field modulus # noqa: E501
a = int("ffffffff00000001000000000000000000000000fffffffffffffffffffffffc", 16)  # Curve coefficient # noqa: E501
b = int("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b", 16)  # Curve coefficient # noqa: E501
n = int("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551", 16)  # Subgroup order # noqa: E501

def i2b32(i: int) -> bytes:  # noqa: D103
    return i.to_bytes(32, "big")

def b2hex(b: bytes) -> str:  # noqa: D103
    return "0x" + b.hex()

def main():  # noqa: D103
    # 1) Generate P-256 keypair
    priv = ec.generate_private_key(ec.SECP256R1())
    pub_nums = priv.public_key().public_numbers()
    qx = i2b32(pub_nums.x)
    qy = i2b32(pub_nums.y)
    d_int = priv.private_numbers().private_value
    d_bytes = i2b32(d_int)
    backend = CoinCurveECCBackend()
    eth_priv = keys.PrivateKey(d_bytes, backend=backend)
    eth_pub = eth_priv.public_key
    signer_addr = eth_pub.to_checksum_address()
    print(f"Private Key: {eth_priv}\nSigner ETH Address: {signer_addr}")

    # 2) Make a 32-byte message hash (SHA-256 of fixed demo message)
    msg = b"hello world"
    h = hashlib.sha256(msg).digest()  # 32 bytes
    print("Message:", msg.decode())

    # Sign *the hash* using ECDSA-P256 with Prehashed(SHA256)
    der_sig = priv.sign(h, ec.ECDSA(Prehashed(hashes.SHA256())))

    # Verify signature
    sig_algo = ec.ECDSA(Prehashed(hashes.SHA256()))
    priv.public_key().verify(der_sig, h, sig_algo) # cryptography.exceptions.InvalidSignature is raised if invalid  # noqa: E501

    r, s = decode_dss_signature(der_sig)
    # store relevant data locally so that we can verify the signature with tools like openssl  # noqa: E501
    #       sig.der
    sig_der = encode_dss_signature(r, s)
    open("sig.der","wb").write(sig_der)
    #       message
    with open("message.txt", "wb") as f:
        f.write(msg)
    #       public key in SubjectPublicKeyInfo PEM
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open("pub.pem", "wb") as f:
        f.write(pub_pem)

    r_b = i2b32(r)
    s_b = i2b32(s)

    # Show the five 32-byte fields
    print("h(ash) =", b2hex(h))
    print("r =", b2hex(r_b))
    print("s =", b2hex(s_b))
    print("qx =", b2hex(qx))
    print("qy =", b2hex(qy))

    # 3) Build precompile input: h | r | s | qx | qy  (exactly 160 bytes)
    assert len(h) == 32
    assert len(r_b) == 32
    assert len(s_b) == 32
    assert len(qx) == 32
    assert len(qy) == 32

    ri = int.from_bytes(r_b, "big")
    si = int.from_bytes(s_b, "big")
    qxi = int.from_bytes(qx, "big")
    qyi = int.from_bytes(qy, "big")

    assert 0 < ri < n and 0 < si < n, "r or s out of range"
    assert 0 <= qxi < p and 0 <= qyi < p, "qx or qy out of range"
    assert pow(qyi, 2, p) == (pow(qxi, 3, p) + (a * qxi) + b) % p, "public key not on curve"  # noqa: E501

    calldata = h + r_b + s_b + qx + qy
    calldata_hex = "0x" + calldata.hex()

    # 4) eth_call to the precompile
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{
            "to": P256_PRECOMPILE,
            "data": calldata_hex,
            #"data": calldata_hex[:-1] + chr(ord(calldata_hex[-1]) ^ 1), # change last char of sig to invalidate it  # noqa: E501
            "gas": hex(100000)
        }, "latest"]
    }

    json_body = json.dumps(payload, separators=(",", ":"))
    curl_cmd = f"curl -fsS -X POST -H 'Content-Type: application/json' --data '{json_body}' {RPC_URL} && echo"  # noqa: E501
    print("\nRun this in bash to reproduce the request:")
    print(curl_cmd, "\n")

    resp = requests.post(RPC_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload)).json()  # noqa: E501
    if "error" in resp:
        raise RuntimeError(resp["error"])

    print("Response:", resp, "", sep="\n")

    out = bytes.fromhex(resp.get("result")[2:]) if resp.get("result") and resp.get("result").startswith("0x") else b""  # noqa: E501
    is_valid = (len(out) == 32 and int.from_bytes(out, "big") == 1)
    print("valid signature? ->", is_valid)

if __name__ == "__main__":
    main()

# client should to be initialized with a genesis where osaka is enabled already

"""
To verify the resulting signature using a 3rd party tool:
    openssl dgst -sha256 -verify pub.pem -signature sig.der message.txt
->  Verified OK
"""
