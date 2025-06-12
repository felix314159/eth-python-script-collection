# fmt: off
"""Helper script to figure out which fork an EIP belongs to."""

import argparse
import datetime

# Map hardforks to their included EIPs
# note: timestamps were acquired via foundry: 'cast block 1 --rpc-url https://eth.llamarpc.com | \grep timestamp'
ETHEREUM_HARDFORKS = {
    "Frontier": {
        "block": 1,
        "timestamp": 1438269988, # Thu, 30 Jul 2015 15:26:28 +0000
        "eips": [],
    },
    "Frontier Thawing": {
        "block": 200_000,
        "timestamp": 1441661589, # Mon, 7 Sep 2015 21:33:09 +0000
        "eips": [],
    },
    "Homestead": {
        "block": 1_150_000,
        "timestamp": 1457981393, # Mon, 14 Mar 2016 18:49:53 +0000
        "eips": [2, 7, 8]
    },
    "DAO Fork": {
        "block": 1_920_000,
        "timestamp": 1469020840, # Wed, 20 Jul 2016 13:20:40 +0000
        "eips": [779],
    },
    "Tangerine Whistle": {
        "block": 2_463_000,
        "timestamp": 1476796771, # Tue, 18 Oct 2016 13:19:31 +0000
        "eips": [150]
    },
    "Spurious Dragon": {
        "block": 2_675_000,
        "timestamp": 1479831344, # Tue, 22 Nov 2016 16:15:44 +0000
        "eips": [155, 160, 161, 170]
    },
    "Byzantium": {
        "block": 4_370_000,
        "timestamp": 1508131331, # Mon, 16 Oct 2017 05:22:11 +0000
        "eips": [100, 140, 196, 197, 198, 211, 214, 649, 658],
    },
    "Constantinople": {
        "block": 7_280_000,
        "timestamp": 1551383524, # Thu, 28 Feb 2019 19:52:04 +0000
        "eips": [145, 1014, 1052, 1234, 1283],  # note: 1283 was never active
    },
    "Petersburg": {
        "block": 7_280_000,
        "timestamp": 1551383524, # Thu, 28 Feb 2019 19:52:04 +0000
        "eips": [145, 1014, 1052, 1234],  # note: same block as Constantinople, just removed 1283
    },
    "Istanbul": {
        "block": 9_069_000,
        "timestamp": 1575764709, # Sun, 8 Dec 2019 00:25:09 +0000
        "eips": [152, 1108, 1344, 1884, 2028, 2200],
    },
    "Muir Glacier": {
        "block": 9_200_000,
        "timestamp": 1577953849, # Thu, 2 Jan 2020 08:30:49 +0000
        "eips": [2384]
    },
    "Berlin": {
        "block": 12_244_000,
        "timestamp": 1618481223, # Thu, 15 Apr 2021 10:07:03 +0000
        "eips": [2565, 2718, 2929, 2930]
    },
    "London": {
        "block": 12_965_000,
        "timestamp": 1628166822, # Thu, 5 Aug 2021 12:33:42 +0000
        "eips": [1559, 3198, 3529, 3541, 3554]
    },
    "Arrow Glacier": {
        "block": 13_773_000,
        "timestamp": 1639079723, # Thu, 9 Dec 2021 19:55:23 +0000
        "eips": [4345]
    },
    "Gray Glacier": {
        "block": 15_050_000,
        "timestamp": 1656586444, # Thu, 30 Jun 2022 10:54:04 +0000
        "eips": [5133]
    },
    "Paris": { # The Merge
        "block": 15_537_394,
        "timestamp": 1663224179, # Thu, 15 Sep 2022 06:42:59 +0000
        "eips": [3675, 4399]
    },
    "Shanghai": {
        "block": 17_034_870,
        "timestamp": 1681338479, # Wed, 12 Apr 2023 22:27:59 +0000
        "eips": [3651, 3855, 3860, 4895, 6049],
    },
    "Cancun": {
        "block": 19_426_587,
        "timestamp": 1710338135, # Wed, 13 Mar 2024 13:55:35 +0000
        "eips": [1153, 4788, 4844, 5656, 6780, 7044, 7045, 7514, 7516],
    },
    "Prague": {
        "block": 22_431_084,
        "timestamp": 1746612311, # Wed, 7 May 2025 10:05:11 +0000
        "eips": [2537, 2935, 6110, 7002, 7251, 7549, 7623, 7642, 7685, 7691, 7702],
    },
    # Below is subject to change
    "Osaka": {
        "block": 9999999999,
        "timestamp": 9999999999,
        "eips": [7594, 7642, 7823, 7825, 7883, 7892, 7917, 7918, 7935],
    },
}

# some of the below ones are irrelevant
INFORMATIONAL_EIPs = [1470, 2069, 2228, 2294, 2458, 2982, 6953, 7783, 7790,
                                 7840, 7870, 7892, 7935, 7938, 7940]

META_EIPs = [1, 4, 233, 606, 607, 608, 609, 779, 867, 1013, 1588, 1679, 1716, 1872,
                        2070, 2378, 2387, 2657, 5069, 5757, 6049, 7199, 7329, 7568, 7569, 7577,
                        7587, 7600, 7607, 7675, 7692, 7723, 7768, 7773, 7808, 7872, 7919, 7927] # 2070 is withdrawn
# categories: networking, interface, core, erc
NETWORKING_EIPs = [8, 627, 706, 778, 868, 1459, 2124, 2364, 2464, 2481, 2976, 4444,
                              4938, 5793, 6122, 7542, 7594, 7636, 7639, 7642, 7801]

INTERFACE_EIPs = [107, 234, 712, 747, 758, 1186, 1193, 1474, 1571, 1803, 1898, 2003,
                             2159, 2256, 2566, 2696, 2700, 2831, 2844, 3014, 3030, 3041, 3045,
                             3046, 3076, 3085, 3091, 3155, 3326, 3709, 5345, 5593, 5749, 5792,
                             6789, 6963, 7713, 7749, 7756, 7867, 7910]
# TODO: add core and erc lists

def check_eip_inclusion(eip_number):
    """Check if an EIP was included in any hardfork."""
    for fork_name, fork_data in ETHEREUM_HARDFORKS.items():
        if eip_number in fork_data["eips"]:
            return fork_name, fork_data
    return None, None

def get_human_readable_timestamp(timestamp: int) -> str:
    """Take timestamp and return human-readable time."""
    dt_object = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    return dt_object.strftime("%a, %d %b %Y %H:%M:%S %z")

def get_eip_title(eip_number: int):
    pass
    # TODO: retrieve title of eip via request

def main():
    """Run."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Check if an Ethereum Improvement Proposal (EIP) was included in any hardfork",
        usage="python eip_checker.py <eip_number>",
    )
    parser.add_argument("eip_number", type=str, help="The EIP number to check")

    # Parse arguments
    args = parser.parse_args()

    if not args.eip_number.isdigit():
        print("You are supposed to pass the eip number as e.g. \"123\" or 123")
        exit(1)
    eip_number = int(args.eip_number)

    # Check if EIP was included in any fork
    fork_name, fork_data = check_eip_inclusion(eip_number)

    if not fork_name:
        # EIP was not included in any fork
        print(f"EIP-{eip_number} has not yet been included in any fork and might not even exist.")
        return

    # EIP was included in a fork
    formatted_date = get_human_readable_timestamp(fork_data["timestamp"])
    print(f"EIP-{eip_number} was included in fork '{fork_name}' on {formatted_date}.")

    # Get all other EIPs in this fork
    all_eips = fork_data["eips"]

    if len(all_eips) == 1:
        print("This was the only EIP included in this fork.")
        return

    print("Other EIPs included in this fork are:")
    for eip in sorted(all_eips):
        if eip == eip_number:
            continue
        print(f"* {eip}")


if __name__ == "__main__":
    main()
