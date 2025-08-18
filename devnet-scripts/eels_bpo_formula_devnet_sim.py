from dataclasses import dataclass  # noqa: D100


@dataclass
class Header:  # noqa: D101
    block_id: int  # e.g. block 5
    timestamp: int

    base_fee_per_gas: int  # api response key: baseFeePerGas
    blob_gas_used: int  # api response key: blobGasUsed
    excess_blob_gas: int  # api response key: excessBlobGas


@dataclass
class Fork:  # noqa: D101
    BLOB_SCHEDULE_TARGET: int
    BLOB_SCHEDULE_MAX: int
    BLOB_BASE_FEE_UPDATE_FRACTION: int  # noqa: N815

    activation_time: int
    activation_slot_id_hex: int


# ------------------------------------------------------------------------------

# these are osaka values in eels, but they could be different for bpo?
MIN_BLOB_GASPRICE = 1
# TARGET_BLOB_GAS_PER_BLOCK IMO should be derived via GAS_PER_BLOB * fork.BLOB_SCHEDULE_TARGET
GAS_PER_BLOB = 2**17  # 131_072

# these are bpo1 in eels, but they dont exist for osaka in eels
BLOB_BASE_COST = 2**13  # 8_192


def taylor_exponential(factor: int, numerator: int, denominator: int) -> int:
    """
    Approximates factor * e ** (numerator / denominator) using
    Taylor expansion.

    Parameters
    ----------
    factor :
        The factor.
    numerator :
        The numerator of the exponential.
    denominator :
        The denominator of the exponential.

    Returns
    -------
    output : `ethereum.base_types.Uint`
        The approximation of factor * e ** (numerator / denominator).

    """
    i = 1
    output = 0
    numerator_accumulated = factor * denominator
    while numerator_accumulated > 0:
        output += numerator_accumulated
        numerator_accumulated = (numerator_accumulated * numerator) // (denominator * i)
        i += 1
    return output // denominator


def calculate_blob_gas_price(excess_blob_gas: int, fork: Fork) -> int:
    """
    Calculate the blob gasprice for a block.

    Parameters
    ----------
    excess_blob_gas :
        The excess blob gas for the block.

    fork :
        The current fork.

    Returns
    -------
    blob_gasprice: `Uint`
        The blob gasprice.

    """
    return taylor_exponential(
        MIN_BLOB_GASPRICE,
        excess_blob_gas,
        fork.BLOB_BASE_FEE_UPDATE_FRACTION,
    )


def calculate_excess_blob_gas(parent_header: Header, fork: Fork) -> int:
    """
    Calculate the excess blob gas for the current block based
    on the gas used in the parent block.

    Parameters
    ----------
    parent_header :
        The parent block of the current block.

    fork :
        The current fork (NOT the fork of the parent block!)

    Returns
    -------
    excess_blob_gas: `ethereum.base_types.U64`
        The excess blob gas for the current block.

    """
    # At the fork block, these are defined as zero.
    excess_blob_gas = 0
    blob_gas_used = 0
    base_fee_per_gas = 0
    TARGET_BLOB_GAS_PER_BLOCK: int = GAS_PER_BLOB * fork.BLOB_SCHEDULE_TARGET  # noqa: N806

    if isinstance(parent_header, Header):
        # After the fork block, read them from the parent header.
        excess_blob_gas = parent_header.excess_blob_gas
        blob_gas_used = parent_header.blob_gas_used
        base_fee_per_gas = parent_header.base_fee_per_gas

    parent_blob_gas = excess_blob_gas + blob_gas_used
    if parent_blob_gas < TARGET_BLOB_GAS_PER_BLOCK:
        return 0

    target_blob_gas_price = GAS_PER_BLOB * calculate_blob_gas_price(
        excess_blob_gas=excess_blob_gas, fork=fork
    )

    base_blob_tx_price = BLOB_BASE_COST * base_fee_per_gas
    if base_blob_tx_price > target_blob_gas_price:
        blob_schedule_delta = fork.BLOB_SCHEDULE_MAX - fork.BLOB_SCHEDULE_TARGET
        return excess_blob_gas + blob_gas_used * blob_schedule_delta // fork.BLOB_SCHEDULE_MAX

    return parent_blob_gas - TARGET_BLOB_GAS_PER_BLOCK


# --------------------------------------------


def main():  # noqa: D103
    # https://github.com/ethpandaops/fusaka-devnets/blob/master/network-configs/devnet-4/metadata/genesis.json
    osaka = Fork(
        BLOB_SCHEDULE_TARGET=6,
        BLOB_SCHEDULE_MAX=9,
        BLOB_BASE_FEE_UPDATE_FRACTION=5_007_716,
        activation_time=1_754_738_304,  # Epoch: 256, Slot 8192   (0x2000) (https://github.com/ethpandaops/fusaka-devnets/blob/e9ed03f24b192ca40f728e41265ef4b443bc878b/network-configs/devnet-4/metadata/config.yaml#L198-L208)
        activation_slot_id_hex=0x2000,
    )
    bpo1 = Fork(
        BLOB_SCHEDULE_TARGET=9,
        BLOB_SCHEDULE_MAX=14,
        BLOB_BASE_FEE_UPDATE_FRACTION=8_832_827,
        activation_time=1_754_836_608,  # Epoch: 512, Slot 16384  (0x4000)
        activation_slot_id_hex=0x4000,
    )
    bpo2 = Fork(
        BLOB_SCHEDULE_TARGET=14,
        BLOB_SCHEDULE_MAX=21,
        BLOB_BASE_FEE_UPDATE_FRACTION=13739630,
        activation_time=1_754_934_912,  # Epoch: 768, Slot 24576  (0x6000)
        activation_slot_id_hex=0x6000,
    )
    bpo3 = Fork(
        BLOB_SCHEDULE_TARGET=21,
        BLOB_SCHEDULE_MAX=32,
        BLOB_BASE_FEE_UPDATE_FRACTION=20_609_697,
        activation_time=1_755_033_216,  # Epoch: 1024, Slot 32768  (0x8000)
        activation_slot_id_hex=0x8000,
    )
    bpo4 = Fork(
        BLOB_SCHEDULE_TARGET=32,
        BLOB_SCHEDULE_MAX=48,
        BLOB_BASE_FEE_UPDATE_FRACTION=31_404_902,
        activation_time=1_755_131_520,  # Epoch: 1280, Slot 40960  (0xA000)
        activation_slot_id_hex=0xA000,
    )
    bpo5 = Fork(
        BLOB_SCHEDULE_TARGET=48,
        BLOB_SCHEDULE_MAX=72,
        BLOB_BASE_FEE_UPDATE_FRACTION=47_107_372,
        activation_time=1_755_229_824,  # EPOCH: 1536, Slot: 1536*32 = 49152  (0xC000)
        activation_slot_id_hex=0xC000,
    )

    forks = [osaka, bpo1, bpo2, bpo3, bpo4, bpo5]


main()

# EXAMPLE: Getting info of block with id 0xa112 of fusaka-devnet-4:
#   curl -s https://rpc.fusaka-devnet-4.ethpandaops.io/ -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0xa112",true],"id":1}'  # noqa: E501, W291
# Note that it is not directly clear which block you want to request if you only know the slot. You kinda have to guess the block and then check whether it refers to the slot you want afaik
