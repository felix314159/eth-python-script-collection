from zlib import crc32

def forkid(genesis_hash_hex, fork_blocks=None, fork_times=None, head=0, ts=0):
    fork_blocks = sorted(fork_blocks or [])
    fork_times  = sorted(fork_times  or [])

    ghex = genesis_hash_hex[2:] if genesis_hash_hex.startswith("0x") else genesis_hash_hex
    genesis_bytes = bytes.fromhex(ghex)
    if len(genesis_bytes) != 32:
        raise ValueError("genesis hash must be 32 bytes")

    c = crc32(genesis_bytes) & 0xFFFFFFFF

    for b in fork_blocks:
        if b <= head:
            c = crc32(b.to_bytes(8, "big"), c) & 0xFFFFFFFF

    for t in fork_times:
        if t <= ts:
            c = crc32(t.to_bytes(8, "big"), c) & 0xFFFFFFFF

    future_ts = [t for t in fork_times  if t > ts]
    if future_ts:
        fork_next = min(future_ts)
    else:
        future_blk = [b for b in fork_blocks if b > head]
        fork_next = min(future_blk) if future_blk else 0

    return c, fork_next

# Relevant EIPs: 2124 and 6122
def main():
    MAINNET_GENESIS = "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
   
    # future fork timestamps (subject to change)
    # TODO: if u add new future fork also add it to the end of fork_times_postmerge
    BPO2 = 1_767_747_671
    BPO1 = 1_765_290_071
    OSAKA = 1_764_798_551

    # timestamps are used instead of block numbers for everything at paris and later
    PRAGUE = 1_746_612_311
    CANCUN = 1_710_338_135
    SHANGHAI = 1_681_338_455
    PARIS_TIME = 1_668_000_000
    
    # block number where fork activated (https://github.com/felix314159/eth-python-script-collection/blob/6269bf000757d18229509afaebfe1180c99e04df/eip-checker.py#L9)
    PARIS = 18_000_000 # EIP-6122: merge netsplit block
    GRAY_GLACIER = 15_050_000
    ARROW_GLACIER = 13_773_000
    LONDON = 12_965_000
    BERLIN = 12_244_000
    MUIR_GLACIER = 9_200_000
    ISTANBUL = 9_069_000
    CONSTANTINOPLE_PETERSBURG = 7_280_000
    BYZANTIUM = 4_370_000
    SPURIOUS_DRAGON = 2_675_000
    TANGERINE_WHISTLE = 2_463_000
    DAO = 1_920_000
    HOMESTEAD = 1_150_000
    UNSYNCED = 0

    test_case_heads = [
                        UNSYNCED, 
                        HOMESTEAD-1, HOMESTEAD, 
                        DAO-1, DAO, 
                        TANGERINE_WHISTLE-1, TANGERINE_WHISTLE,
                        SPURIOUS_DRAGON-1, SPURIOUS_DRAGON,
                        BYZANTIUM-1, BYZANTIUM,
                        CONSTANTINOPLE_PETERSBURG-1, CONSTANTINOPLE_PETERSBURG,
                        ISTANBUL-1, ISTANBUL,
                        MUIR_GLACIER-1, MUIR_GLACIER,
                        BERLIN-1, BERLIN,
                        LONDON-1, LONDON,
                        ARROW_GLACIER-1, ARROW_GLACIER,
                        GRAY_GLACIER-1, GRAY_GLACIER,
                        PARIS-1, PARIS,
                       ]
    
    # ----------------------------- Test Cases (cases 0-13 are from EIP-2124) ---------------------------------------

    # 0) Test Case: Unsynced
    test_id = 0
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xfc64ec04
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {0, ID{Hash: 0xfc64ec04, Next: 1150000}}

    # -------------------------------------------------------------------------------------------

    # 1) Test Case: Last Frontier block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xfc64ec04
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {1149999, ID{Hash: 0xfc64ec04, Next: 1150000}}

    # -------------------------------------------------------------------------------------------

    # 2) Test Case: First Homestead block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x97c2c34c
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {1150000, ID{Hash: 0x97c2c34c, Next: 1920000}}

    # -------------------------------------------------------------------------------------------

    # 3) Test Case: Last Homestead block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x97c2c34c
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {1919999, ID{Hash: 0x97c2c34c, Next: 1920000}}

    # -------------------------------------------------------------------------------------------

    # 4) Test Case: First DAO block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x91d1f948
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {1920000, ID{Hash: 0x91d1f948, Next: 2463000}}

    # -------------------------------------------------------------------------------------------

    # 5) Test Case: Last DAO block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x91d1f948
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {2462999, ID{Hash: 0x91d1f948, Next: 2463000}}

    # -------------------------------------------------------------------------------------------

    # 6) Test Case: First Tangerine Whistle block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x7a64da13
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {2463000, ID{Hash: 0x7a64da13, Next: 2675000}}

    # -------------------------------------------------------------------------------------------

    # 7) Test Case: Last Tangerine Whistle block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x7a64da13
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {2674999, ID{Hash: 0x7a64da13, Next: 2675000}}

    # -------------------------------------------------------------------------------------------

    # 8) Test Case: First Spurious Dragon block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x3edd5b10
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {2675000, ID{Hash: 0x3edd5b10, Next: 4370000}}
    
    # -------------------------------------------------------------------------------------------

    # 9) Test Case: Last Spurious Dragon block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x3edd5b10
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {4369999, ID{Hash: 0x3edd5b10, Next: 4370000}}

    # -------------------------------------------------------------------------------------------

    # 10) Test Case: First Byzantium block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xa00bc324
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {4370000, ID{Hash: 0xa00bc324, Next: 7280000}}

    # -------------------------------------------------------------------------------------------

    # 11) Test Case: Last Byzantium block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xa00bc324
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {7279999, ID{Hash: 0xa00bc324, Next: 7280000}}

    # -------------------------------------------------------------------------------------------

    # 12) Test Case: First Constantinople/Petersburg block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x668db0af
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {7280000, ID{Hash: 0x668db0af, Next: 9069000}}

    # -------------------------------------------------------------------------------------------

    # 13) Test Case: Last Constantinople/Petersburg block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x668db0af
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {9068999, ID{Hash: 0x668db0af, Next: 9069000}}

    # -------------------------------------------------------------------------------------------

    # 14) Test Case: First Istanbul block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x879d6e30
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {9069000, ID{Hash: 0x879d6e30, Next: 9200000}}

    # -------------------------------------------------------------------------------------------

    # 15) Test Case: Last Istanbul block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x879d6e30
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {9199999, ID{Hash: 0x879d6e30, Next: 9200000}}

    # -------------------------------------------------------------------------------------------

    # 16) Test Case: First Muir Glacier block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xe029e991
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {9200000, ID{Hash: 0xe029e991, Next: 12244000}}

    # -------------------------------------------------------------------------------------------

    # 17) Test Case: Last Muir Glacier block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xe029e991
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {12243999, ID{Hash: 0xe029e991, Next: 12244000}}

    # -------------------------------------------------------------------------------------------

    # 18) Test Case: First Berlin block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x0eb440f6
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#03x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {12244000, ID{Hash: 0x0eb440f6, Next: 12965000}}
    
    # -------------------------------------------------------------------------------------------

    # 19) Test Case: Last Berlin block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xeb440f6
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {12964999, ID{Hash: 0x0eb440f6, Next: 12965000}}

    # -------------------------------------------------------------------------------------------

    # 20) Test Case: First London block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xb715077d
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {12965000, ID{Hash: 0xb715077d, Next: 13773000}}

    # -------------------------------------------------------------------------------------------

    # 21) Test Case: Last London block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0xb715077d
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {13772999, ID{Hash: 0xb715077d, Next: 13773000}}

    # -------------------------------------------------------------------------------------------

    # 22) Test Case: First Arrow Glacier block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER, GRAY_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x20c327fc
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {13773000, ID{Hash: 0x20c327fc, Next: 15050000}}

    # -------------------------------------------------------------------------------------------

    # 23) Test Case: Last Arrow Glacier block
    test_id += 1
    head = test_case_heads[test_id]
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER, GRAY_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, head=head, ts=0)
    
    expected_forkid = 0x20c327fc
    expected_next = fork_blocks[-1]
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next, f"wanted {expected_next} got {n}"
    # {15049999, ID{Hash: 0x20c327fc, Next: 15050000}}

    # --------------------------- Timestamp-based from here onwards (test cases from EIP-6122) --

    # 24) Test Case: First Gray Glacier block
    test_id += 1
    head = GRAY_GLACIER
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER, GRAY_GLACIER, PARIS]
    ts = GRAY_GLACIER
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[PARIS], head=head, ts=ts)
    
    expected_forkid = 0xf0afd0e3
    expected_next = PARIS
    print(f"Test #{test_id}: {{{head}, ID{{Hash: 0x{h:08x}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {15050000, 0, ID{Hash: checksumToBytes(0xf0afd0e3), Next: 18000000}}

    # -------------------------------------------------------------------------------------------

    # 25) Test Case: First Merge Start block
    test_id += 1
    head = PARIS # head will not change anymore as this is the last block based fork, we expand fork_times from here onwards
    ts = PARIS
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[PARIS_TIME], head=head, ts=ts)
    
    expected_forkid = 0x4fb8a872
    expected_next = PARIS_TIME
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {18000000, ID{Hash: 0x4fb8a872, Next: 1668000000}}

    # -------------------------------------------------------------------------------------------

    # 26) Test Case: Last Merge block
    test_id += 1
    ts = 20_000_000
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[PARIS_TIME], head=head, ts=ts)
    
    expected_forkid = 0x4fb8a872
    expected_next = PARIS_TIME
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {20000000, ID{Hash: 0x4fb8a872, Next: 1668000000}}

    # -------------------------------------------------------------------------------------------

    # 27) Test Case: First Shanghai block (not from EIP-6122 where it expects 0xc1fdf181)
    test_id += 1
    ts = SHANGHAI
    fork_blocks = [HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER, GRAY_GLACIER]
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN], head=head, ts=ts)
    
    expected_forkid = 0xdce96c2d # problem: wanted 0xdce96c2d got 0xfaeac109
    expected_next = CANCUN
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1681338455, ID{Hash: 0xdce96c2d, Next: 1710338135}}

    # -------------------------------------------------------------------------------------------

    # 28) Test Case: Last Shanghai block
    test_id += 1
    ts = CANCUN - 1
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN], head=head, ts=ts)
    
    expected_forkid = 0xdce96c2d
    expected_next = CANCUN
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1710338134, ID{Hash: 0xdce96c2d, Next: 1710338135}}

    # ---------------------------------------- One EIP-6122 test -----------------------------------------

    # 29) Local is mainnet Withdrawals, remote announces the same. No future fork is announced.
    test_id += 1
    ts = 1_668_000_001
    h, n = forkid(MAINNET_GENESIS, fork_blocks=[HOMESTEAD, DAO, TANGERINE_WHISTLE, SPURIOUS_DRAGON, BYZANTIUM, CONSTANTINOPLE_PETERSBURG, ISTANBUL, MUIR_GLACIER, BERLIN, LONDON, ARROW_GLACIER, GRAY_GLACIER, PARIS], fork_times=[PARIS_TIME], head=head, ts=ts)
    
    expected_forkid = 0xc1fdf181
    expected_next = 0
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1668000001, ID{Hash: 0xc1fdf181, Next: 0}}

    # ---------------------------------------- More test cases --------------------------------------------

    # 30) First Cancun
    test_id += 1
    ts = CANCUN
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE], head=head, ts=ts)
    
    expected_forkid = 0x9f3d2254
    expected_next = PRAGUE
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1710338135, ID{Hash: 0x9f3d2254, Next: 1746612311}}
    
    # ----------------------------------------------------------------------------------------------------

    # 31) Last Cancun
    test_id += 1
    ts = PRAGUE - 1
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE], head=head, ts=ts)
    
    expected_forkid = 0x9f3d2254
    expected_next = PRAGUE
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1746612310, ID{Hash: 0x9f3d2254, Next: 1746612311}}

    # ----------------------------------------------------------------------------------------------------

    # 32) First Prague
    test_id += 1
    ts = PRAGUE
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA], head=head, ts=ts)
    
    expected_forkid = 0xc376cf8b
    expected_next = OSAKA
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1746612311, ID{Hash: 0xc376cf8b, Next: 1764798551}}

    # ----------------------------------------------------------------------------------------------------

    # 33) Last Prague
    test_id += 1
    ts = OSAKA - 1
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA], head=head, ts=ts)
    
    expected_forkid = 0xc376cf8b
    expected_next = OSAKA
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1764798550, ID{Hash: 0xc376cf8b, Next: 1764798551}}

    # ----------------------------------------------------------------------------------------------------

    # 34) Test Case: First Osaka
    test_id += 1
    ts = OSAKA
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA, BPO1], head=head, ts=ts)
    
    expected_forkid = 0x5167e2a6
    expected_next = BPO1
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1764798551, ID{Hash: 0x5167e2a6, Next: 1765290071}}

    # -----------------------------------------------------------------------------------------------------

    # 35) Test Case: Last Osaka
    test_id += 1
    ts = BPO1 - 1
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA, BPO1], head=head, ts=ts)
    
    expected_forkid = 0x5167e2a6
    expected_next = BPO1
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1765290070, ID{Hash: 0x5167e2a6, Next: 1765290071}}

    # -----------------------------------------------------------------------------------------------------

    # 36) Test Case: First BPO1
    test_id += 1
    ts = BPO1
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA, BPO1, BPO2], head=head, ts=ts)
    
    expected_forkid = 0xcba2a1c0
    expected_next = BPO2
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1765290071, ID{Hash: 0xcba2a1c0, Next: 1767747671}}

    # -----------------------------------------------------------------------------------------------------

    # 37) Last BPO1
    test_id += 1
    ts = BPO2 - 1
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA, BPO1, BPO2], head=head, ts=ts)
    
    expected_forkid = 0xcba2a1c0
    expected_next = BPO2
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1767747670, ID{Hash: 0xcba2a1c0, Next: 1767747671}}

    # -----------------------------------------------------------------------------------------------------

    # 38) First BPO2, Unknown next fork
    test_id += 1
    ts = BPO2
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA, BPO1, BPO2], head=head, ts=ts)
    
    expected_forkid = 0x07c9462e
    expected_next = 0
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {1767747671, ID{Hash: 0x7c9462e, Next: 0}}

    # -----------------------------------------------------------------------------------------------------

    # 39) Future BPO2, Unknown next fork
    test_id += 1
    ts = 2_000_000_000
    h, n = forkid(MAINNET_GENESIS, fork_blocks=fork_blocks, fork_times=[SHANGHAI, CANCUN, PRAGUE, OSAKA, BPO1, BPO2], head=head, ts=ts)
    
    expected_forkid = 0x07c9462e
    expected_next = 0
    print(f"Test #{test_id}: {{{ts}, ID{{Hash: {hex(h)}, Next: {n}}}}}")
    assert h == expected_forkid, f"wanted {expected_forkid:#02x} got {hex(h)}"
    assert n == expected_next,   f"wanted {expected_next} got {n}"
    # {2000000000, ID{Hash: 0x7c9462e, Next: 0}}

if __name__ == "__main__":
    main()
