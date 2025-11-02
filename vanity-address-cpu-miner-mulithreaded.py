import multiprocessing as mp
import secrets
from eth_keys import keys # pip3 install eth-keys --break-system-packages

# secp256k1 curve order (private must be smaller than this)
SECP256K1_N = int(
    "0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141", 16
)

def generate_privkey():
    """Technically, the only requirement is that the key is smaller than the curve order, but I also avoid the smallest and largest trillion possible keys on purpose."""
    amount_skipped_keys = 10**12

    while True:
        # generate key
        privkey_bytes = secrets.token_bytes(32)
        privkey_int = int.from_bytes(privkey_bytes)

        # ensure it satisfies requirements
        if privkey_int < amount_skipped_keys:
            print("Key is very small, might be a bad idea to use this one. Trying again..")
            continue
        if privkey_int > SECP256K1_N - amount_skipped_keys:
            print("Key is very large, might be a bad idea to use this one. Trying again..")
            continue

        # derive pubkey
        pk = keys.PrivateKey(privkey_bytes)
        
        # derive address
        addr = pk.public_key.to_checksum_address()

        # return privkey, address
        return privkey_bytes, addr


def _mine_vanity(vanityword: str, stop: mp.Event, out_q: mp.Queue):
    while True:
        privkey, addr = generate_privkey()
        if addr[2:].lower().startswith(vanityword) or addr.lower().endswith(vanityword):
            # send result to parent and signal stop
            out_q.put((privkey.hex(), addr))
            stop.set()
            return


def mine_vanity_address(vanityword: str):
    assert len(vanityword) <= 8, "Try a shorter vanity word" # technically 40 lmao

    try:
        int(vanityword, 16)
    except ValueError:
        raise AssertionError(f"'{vanityword}' is not a valid hexadecimal string")

    # our mining is case-insensitive
    vanityword = vanityword.lower()

    # determine amount of available threads
    threads_amount = mp.cpu_count()

    print(f"Mining address that starts or ends with '{vanityword}' using {threads_amount} threads...")

    # ----------------- Multithreading -------------------

    # create processes
    stop = mp.Event()
    out_q = mp.Queue()
    procs = []
    for _ in range(threads_amount):
        p = mp.Process(target=_mine_vanity, args=(vanityword, stop, out_q))
        procs.append(p)
        p.start()

    # wait until the first process succeeds
    priv_hex, addr = out_q.get()
    
    # stop all other workers
    stop.set()
    for p in procs:
        p.join(timeout=0.2)
    for p in procs:
        if p.is_alive():
            p.terminate()

    return priv_hex, addr


def main():
    # privkey, addr = generate_privkey()
    # print(f"Private Key:\t{privkey.hex()}\nAddress:\t{addr}")

    # --------- Vanity address miner ------------
    priv_hex, addr = mine_vanity_address("abcd")
    print(f"Private Key:\t{priv_hex}\nAddress:\t{addr}")


main()
"""
Private Key:    78d1b8e33e3913ef8911506ebadfac79de8068cbb0331f9a45d92d2ade2efc1f
Address:        0xABcde97FC1D242FC3C8b4c126718E5e2b416E6DF

Verify with e.g. ` cast wallet address --private-key 78d1b8e33e3913ef8911506ebadfac79de8068cbb0331f9a45d92d2ade2efc1f `
"""
