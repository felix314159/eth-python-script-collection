# PREREQ:
#    sudo apt install python3-rlp python3-pycryptodome
#    sudo pip3 install eth-hash eth-hash[pycryptodome] --break-system-packages

# rlp
import rlp
from rlp.sedes import big_endian_int, List

# eth-hash (keccak256)
from eth_hash.auto import keccak as keccak256

# --------------------- Unit tests ---------------------
def test_rlp_unittest():
    error_msg = "Failed RLP test!"
    assert rlp.encode(1234) == b'\x82\x04\xd2', error_msg
    assert rlp.encode([1,[2,[]]]) == b'\xc4\x01\xc2\x02\xc0', error_msg
    assert rlp.decode(b'\xc4\x01\xc2\x02\xc0', List([big_endian_int, [big_endian_int, []]])) == (1, (2, ())), error_msg

    print("Successfully passed all RLP tests.")


def test_keccak256():
    error_msg = "Failed Keccak256 test!"
    assert keccak256(b'') == b"\xc5\xd2F\x01\x86\xf7#<\x92~}\xb2\xdc\xc7\x03\xc0\xe5\x00\xb6S\xca\x82';{\xfa\xd8\x04]\x85\xa4p", error_msg
    assert keccak256_hex("abc") == "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45", error_msg

    print("Successfully passed all Keccak256 tests.")


# -------------------------------- Helper functions ------------------------------
def keccak256_hex(input):
    """ Keccak256 wrapper that can handle input either as bytes or as string. Returns result as hex string. """
    if isinstance(input, str):
        input = bytes(input, encoding='utf-8')
    result_bytes = keccak256(input)
    return result_bytes.hex()


# -------------------------------- Contract address prediction ---------------------------

# Version 1: CREATE	keccak256(rlp.encode([sender, nonce]))[-40:]
def contract_CREATE(sender: str, nonce: int):
    sender = bytes.fromhex(sender)

    rlp_input = [sender, nonce]
    rlp_encoded = rlp.encode(rlp_input)

    untrimmed_result = keccak256_hex(rlp_encoded)
    result = untrimmed_result[-40:]

    return result


# Version 2: CREATE2 	keccak256(0xFF ++ sender ++ salt ++ keccak256(init_code))[-40:]
def contract_CREATE2(sender: str, salt: str, init_code: str):
    pass
    # TODO: implement


def main():
    # run unit tests
    test_rlp_unittest()
    test_keccak256()

    # testing contract prediction results
    #    CREATE
    example_create = contract_CREATE(sender="6ac7ea33f8831ea9dcc53393aaa88b25a785dbf0", nonce=0)
    assert example_create == "cd234a471b72ba2f1ccf0a70fcaba648a5eecd8d", "CREATE example failed!"

    #    CREATE2
    # TODO

    print("Successfully passed all contract address pre-calculation tests.")


main()

