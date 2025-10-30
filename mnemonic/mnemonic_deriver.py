# derives ethereum mnemonics (no bip_utils)  # noqa: D100

# PREREQ:
#   pip3 install eth-account --break-system-packages

import hmac
import hashlib
import string
import unicodedata
from secrets import choice, randbelow # cryptographically secure derivation of values in [0,2047] for generating mnemonics, "most secure source of randomness that your operating system provides": https://docs.python.org/3/library/secrets.html#random-numbers
from typing import Tuple, List

from eth_account import Account  # type: ignore
from eth_keys import keys  # type: ignore


# bip-39 seed generation
def mnemonic_to_seed(*, mnemonic: str, use_empty_passphrase: bool = False) -> bytes:
    specced_prefix = "mnemonic" # len 8

    if use_empty_passphrase:
        passphrase = ""
    else:
        # salt should be about 16 or more bytes (https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac)
        # i will go for 32 bytes salt, mnemonic prefix is 8 chars already so generate a passphrase of 24 ascii chars
        alphabet = string.ascii_letters + string.digits
        passphrase = ''.join(choice(alphabet) for _ in range(24))

    mnemonic = unicodedata.normalize("NFKD", mnemonic.strip())
    passphrase = unicodedata.normalize("NFKD", passphrase)

    if not use_empty_passphrase:
        print("Mnemonic passphrase:", passphrase) # given the same mnemonic u will derive different keys depending on which passphrase u chose

    salt = specced_prefix + passphrase # https://en.bitcoin.it/wiki/BIP_0039 , read "From mnemonic to seed"
    return hashlib.pbkdf2_hmac(
        "sha512", # used as pseudo random function
        mnemonic.encode("utf-8"),
        salt.encode("utf-8"),
        2048, # iteration count
        dklen=64, # length of derived key in bytes
    )


# curve order for secp256k1
#   decimal: 115792089237316195423570985008687907852837564279074904382605163141518161494337
SECP256K1_N = int(
    "0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141", 16
)

def hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()

def ser32(i: int) -> bytes:
    return i.to_bytes(4, "big")

def ser256(i: int) -> bytes:
    return i.to_bytes(32, "big")

def parse256(b: bytes) -> int:
    return int.from_bytes(b, "big")

def point_compressed_from_priv(k_int: int) -> bytes:
    pk = keys.PrivateKey(ser256(k_int))
    return pk.public_key.to_compressed_bytes()  # 33 bytes 0x02/0x03 + X

def bip32_master_key(seed: bytes) -> Tuple[int, bytes]:
    I = hmac_sha512(b"Bitcoin seed", seed)
    IL, IR = I[:32], I[32:]
    k_int = parse256(IL)
    if not (1 <= k_int < SECP256K1_N):
        raise ValueError("Invalid master key generated.")
    return k_int, IR

def ckd_priv(k_par: int, c_par: bytes, index: int) -> Tuple[int, bytes]:
    if index >= 0x80000000:
        data = b"\x00" + ser256(k_par) + ser32(index)
    else:
        data = point_compressed_from_priv(k_par) + ser32(index)

    I = hmac_sha512(c_par, data)
    IL, IR = I[:32], I[32:]
    child = (parse256(IL) + k_par) % SECP256K1_N
    if parse256(IL) >= SECP256K1_N or child == 0:
        raise ValueError("Invalid child key derived.")
    return child, IR

def derive_priv_for_path(k_master: int, c_master: bytes, path: str) -> Tuple[int, bytes]:
    if not path.startswith("m/"):
        raise ValueError("Path must start with 'm/'.")
    segments = path.lstrip("m/").split("/") if path != "m" else []
    k, c = k_master, c_master
    for seg in segments:
        hardened = seg.endswith("'")
        idx_str = seg[:-1] if hardened else seg
        if not idx_str.isdigit():
            raise ValueError(f"Invalid path segment: {seg}")
        idx = int(idx_str)
        if idx < 0 or idx > 0x7FFFFFFF:
            raise ValueError(f"Invalid index in segment: {seg}")
        if hardened:
            idx |= 0x80000000
        k, c = ckd_priv(k, c, idx)
    return k, c

# ethereum coin type 60 (greek symbol for ether is Ξ, which is 60 in greek numerals)
def bip44_eth_path(account: int, change: int, index: int) -> str:
    return f"m/44'/60'/{account}'/{change}/{index}"

# generates x many Ethereum (BIP-44) accounts from a 12-word mnemonic
# you can pass the mnemonic as string (1 space between words) or as list of 12 strings
def generate_x_keys(*, mnemonic: str | List[str], x: int = 1, use_empty_passphrase: bool = False, print_privkey: bool = True, print_nothing_overwrite: bool = False) -> List[dict]:
    if isinstance(mnemonic, str):
        mnemonic = mnemonic.strip()
        assert mnemonic.count(" ") == 11, "Please enter a 12-word mnemonic divided by single spaces"
    elif isinstance(mnemonic, list) and all(isinstance(s, str) for s in mnemonic):
        mnemonic = " ".join(mnemonic).lower()
    else:
        print("invalid mnemonic type")
        exit(1)

    assert isinstance(mnemonic, str)
    assert x > 0

    seed = mnemonic_to_seed(mnemonic=mnemonic, use_empty_passphrase=use_empty_passphrase)
    k_m, c_m = bip32_master_key(seed)

    accounts = []
    for i in range(x):
        path = bip44_eth_path(account=0, change=0, index=i)
        k_i, _ = derive_priv_for_path(k_m, c_m, path)
        priv_bytes = ser256(k_i)
        acct = Account.from_key(priv_bytes)

        rec = {
            "index": i,
            "address": acct.address,
            "private_key": acct.key.hex(),
        }
        accounts.append(rec)

    if not print_nothing_overwrite:
        for acc in accounts:
            print(f"Account #{acc['index']}:")
            print(f"  Address:     {acc['address']}")
            if print_privkey:
                print(f"  Private Key: {acc['private_key']}\n")

    return accounts

def load_bip39_wordlist(filename: str) -> List[str]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            wordlist = f.read().strip().splitlines()
    except Exception as e:
        print("failed to open ./" + filename)
        exit(1)

    if len(wordlist) != 2048:
        print(filename, "is supposed to contain 2048 lines, but yours does not")
        exit(1)

    return wordlist

def get_random_word_from_wordlist(wordlist: List[str]) -> str:
    #assert len(wordlist) == 2048 # can be commented out for performance when spammed, but getting length is O(1) and AFAIK assert number1,number2 is very fast too
    return wordlist[randbelow(2048)]

def generate_valid_mnemonic(wordlist: List[str], verbose: bool = True) -> List[str]:
    # spam generations until you get a valid mnemonic
    while True:
        mnemonic = [get_random_word_from_wordlist(wordlist) for _ in range(12)]
        is_valid = is_valid_mnemonic(mnemonic)
        if is_valid:
            break
        if verbose:
            print("Invalid:", mnemonic)

    return mnemonic


# takes list that contains 12 strings (from bip-39 english mnemonic list) and tells you whether these words in this order are a valid mnemonic
# assumes ./english.txt exists (take it from here: https://github.com/bitcoin/bips/blob/c9a6ca6297eb8de850f6b64dafb8e60ee9b64d66/bip-0039/english.txt), contains 2048 split across 2048 lines
def is_valid_mnemonic(wordlist) -> bool:
    if not isinstance(wordlist, list) or len(wordlist) != 12:
        return False

    words = [unicodedata.normalize("NFKD", (w or "").strip().lower()) for w in wordlist]

    # load local wordlist
    wordlist = load_bip39_wordlist("english-bip39.txt")

    # build index map
    idx_map = {w: i for i, w in enumerate(wordlist)}
    try:
        indices = [idx_map[w] for w in words]
    except Exception as e:
        print("failed to build index map")
        print(e)
        return False

    # 12 words = 132 bits (128 entropy + 4 checksum)
    bitstr = "".join(format(i, "011b") for i in indices)
    ent_bits, cs_bits = bitstr[:128], bitstr[128:]

    # convert entropy bits to bytes
    if len(ent_bits) != 128 or len(cs_bits) != 4:
        return False
    entropy_int = int(ent_bits, 2)
    entropy = entropy_int.to_bytes(16, "big")

    # compute checksum
    digest = hashlib.sha256(entropy).digest()
    expected_cs = format(digest[0], "08b")[:4]

    return cs_bits == expected_cs


def mine_address(vanityword: str):
    assert len(vanityword) <= 8, "Try a shorter vanity word" # technically 40 lmao

    try:
        int(vanityword, 16)
    except ValueError:
        raise AssertionError(f"'{vanityword}' is not a valid hexadecimal string")

    print(f"Mining address that starts or ends with '{vanityword}'...")

    wordlist = load_bip39_wordlist("english-bip39.txt")
    # we roll with the first valid mnemonic we randomly generate
    mnemonic_list = generate_valid_mnemonic(wordlist, False) # not verbose
    mnemonic = " ".join(mnemonic_list).lower()
    print("Mnemonic:", mnemonic_list)

    seed = mnemonic_to_seed(mnemonic=mnemonic, use_empty_passphrase=False)
    k_m, c_m = bip32_master_key(seed)
    # x must be <= 2**31 - 1, after that you would need to increase account by 1. but irrelevant here
    x = (2**31) - 1
    for i in range(x):
        path = bip44_eth_path(account=0, change=0, index=i)
        k_i, _ = derive_priv_for_path(k_m, c_m, path)
        priv_bytes = ser256(k_i)
        acct = Account.from_key(priv_bytes)

        if acct.address.startswith(vanityword) or acct.address.endswith(vanityword):
            print("Address #" + str(i))
            privkey = acct.key.hex()
            return mnemonic, acct.address, privkey
            
    print("Failed to find vanity address. Just run this again.")
    exit(1)

def main():
    # Example 1: official BIP-39 test vector
    # mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    # mnemonic_list = ["abandon"]*11 + ["about"]
    # generate_x_keys(mnemonic=mnemonic, x=5, use_empty_passphrase=True)

    # verify correctness with 3rd party tool, e.g. foundry cast:
    #       Address #0:        cast wallet address --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" --mnemonic-derivation-path "m/44'/60'/0'/0/0"
    #       -> 0x9858EfFD232B4033E47d90003D41EC34EcaEda94
    #       Private key #0:    cast wallet private-key --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" --mnemonic-derivation-path "m/44'/60'/0'/0/0"
    #       -> 0x1ab42cc412b618bdea3a599e3c9bae199ebf030895b039e9db1e30dafb12b727
    #
    #       Address #4:        cast wallet address --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" --mnemonic-derivation-path "m/44'/60'/0'/0/4"
    #       -> 0x51cA8ff9f1C0a99f88E86B8112eA3237F55374cA
    #       Private key #4:    cast wallet private-key --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" --mnemonic-derivation-path "m/44'/60'/0'/0/4"
    #       -> 0xbd443149113127d73c350d0baeceedd2c83be3f10e3d57613a730649ddfaf0c0
    #  Example where the passphrase is not empty:
    #       Go get private key of address #10 of ['device', 'doll', 'dune', 'trend', 'expose', 'wheel', 'hat', 'crane', 'empty', 'trouble', 'snap', 'unfair'] with mnemonic passphrase: e6oM3Vx5cW50sgNAr30M2FF4
    #           Run this:      cast wallet private-key --mnemonic "device doll dune trend expose wheel hat crane empty trouble snap unfair" --mnemonic-derivation-path "m/44'/60'/0'/0/10" --mnemonic-passphrase "e6oM3Vx5cW50sgNAr30M2FF4"
    #       -> 0x7f4a5eb597f68f0bd179a066aa618dec60d78fb4021f7fc0bd846a61c9ad66a0

    # Example 2: reth dev pre-alloc mnemonic
    # mnemonic = "test " * 11 + "junk"
    # generate_x_keys(mnemonic=mnemonic, x=20, use_empty_passphrase=True)

    # Note: Never use examples from above in prod and avoid using empty passphrase. Anyway, you can use e.g. go-ethereum to safely store your private key in an encrypted keystore file, but you have to remove the 0x prefix.
    # Example: 
    # First store 1ab42cc412b618bdea3a599e3c9bae199ebf030895b039e9db1e30dafb12b727 in ~/Downloads/examplekey.txt
    # Then run:
    #   geth account import ~/Downloads/examplekey.txt
    # After entering pw twice it will create the keystore file in ~/.ethereum/keystore

    # ----------------------------------------------------------------------------------

    # Example 3: Given a mnemonic wordlist, check whether this is a valid bip39 mnemonic
    # mnemonic_wordlist = ["abandon"]*11 + ["about"]
    # is_valid = is_valid_mnemonic(mnemonic_wordlist)
    # print(is_valid) # True

    # mnemonic_wordlist2 = ["abandon"]*12
    # is_valid = is_valid_mnemonic(mnemonic_wordlist2)
    # print(is_valid) # False

    # ----------------------------------------------------------------------------------

    # Example 4: Generate a random but valid mnemonic
    # wordlist = load_bip39_wordlist("english-bip39.txt")
    # mnemonic = generate_valid_mnemonic(wordlist)
    # print("\nValid:", mnemonic)
    # generate_x_keys(mnemonic=mnemonic, x=1, use_empty_passphrase=False, print_privkey=False)
    
    # ----------------------------------------------------------------------------------

    # Example 5: Find a valid mnemonic where the first derived address starts or ends with a hex-string of your choice (vanity address calculator)
    mnemonic, address, privkey = mine_address("deadbeef")
    print(address, privkey)


if __name__ == "__main__":
    main()
# probably a good idea to not use any of this in prod

"""
python mnemonic_deriver.py 
Mining address that starts or ends with '42'...
Mnemonic: ['devote', 'cycle', 'dinner', 'bread', 'cake', 'castle', 'square', 'fresh', 'file', 'elbow', 'aunt', 'cactus']
Mnemonic passphrase: W2kHD4v1AelTzPfTZSjJjl42
0x55D5193263d69BcAAF6a096EdD79588d29DB4242 e105e98e9367bec9912240fbda9ea43729ade510b3917cc626398551869b761d

Kinda funny how even the passphrase has a 42 suffix, and the address suffix has double 42 even though it searched for just a single 42
"""
