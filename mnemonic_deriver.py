# derives ethereum mnemonics # noqa: D100

# PREREQ:
#   pip3 install bip-utils --break-system-packages
#   pip3 install eth-account --break-system-packages

import hashlib

from bip_utils import Bip39SeedGenerator, Bip44, Bip44Changes, Bip44Coins  # type: ignore
from eth_account import Account  # type: ignore


# generates valid keys
def generate_x_keys(mnemonic: str, x: int = 1):
    mnemonic = mnemonic.strip()  # remove prefix and suffix spaces
    assert mnemonic.count(" ") == 11, "Please enter a 12-word mnemonic divided by single spaces"
    assert x > 0

    # generate seed from mnemonic
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    # create BIP-44 wallet for ethereum
    wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)

    # derive first x accounts
    accounts = []
    for i in range(x):
        derived = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
        account = {
            "index": i,
            "address": derived.PublicKey().ToAddress(),
            "private_key": derived.PrivateKey().Raw().ToHex(),
        }
        accounts.append(account)

    for acc in accounts:
        print(f"Account #{acc['index']}:")
        print(f"  Address:     {acc['address']}")
        print(f"  Private Key: {acc['private_key']}\n")


# generates keys from invalid mnemonic (do not use for production)
# it will derive the same accounts as the other function given a valid mnemonic tho
def allow_invalid_mnemonic(mnemonic: str, x: int = 1):
    # generate seed from mnemonic without validation
    encoding = "utf-8"
    password = mnemonic.encode(encoding)
    salt = b"mnemonic" + "".encode(encoding)  # empty passphrase
    seed = hashlib.pbkdf2_hmac("sha512", password, salt, 2048)

    # create BIP44 master key for Ethereum
    bip44_mst = Bip44.FromSeed(
        seed, Bip44Coins.ETHEREUM
    )  # https://github.com/ebellocchia/bip_utils/blob/608a0ee3708fde3e8937983b6990cd11311b5e7e/readme/bip44.mdhttps://github.com/ebellocchia/bip_utils/blob/608a0ee3708fde3e8937983b6990cd11311b5e7e/readme/bip44.md

    # get account 0
    bip44_acc = bip44_mst.Purpose().Coin().Account(0)

    # get external chain
    bip44_chain = bip44_acc.Change(Bip44Changes.CHAIN_EXT)

    # generate x addresses
    for i in range(x):
        # explanation of bip44 path structure (e.g. m/44'/60'/0'/0/0 or m/44'/60'/0'/0/19):
        # source: https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki
        #   m   -> master           (root of tree)
        #   44  -> purpose          (bip44 standard)
        #   60  -> coin type        (ethereum)
        #   0   -> account
        #   0   -> change           (0=external, 1=internal)
        #   0   -> address index    (which address under a given account, we go from 0 to x)

        # get address at index i
        bip44_addr = bip44_chain.AddressIndex(i)

        # get private key
        private_key_bytes = bip44_addr.PrivateKey().Raw().ToBytes()

        # create ethereum account
        acct = Account.from_key(private_key_bytes)

        print(f"Account #{i}:")
        # print(f"  Path:        m/44'/60'/0'/0/{i}")
        print(f"  Address:     {acct.address}")
        print(f"  Private Key: {acct.key.hex()}\n")


def main():
    # here is an official example mnemonic, you can not just chose random words. never use keys derived from this in production  # noqa: E501
    # mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"  # noqa: E501
    # generate_x_keys(mnemonic=mnemonic, x=20)

    # example for using an invalid mnemonic (reth dev)
    mnemonic = "test " * 12
    allow_invalid_mnemonic(mnemonic=mnemonic, x=20)


main()
