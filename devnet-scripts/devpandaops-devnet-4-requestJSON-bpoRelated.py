from typing import Any  # noqa: D100

import requests


def get_data_of_slot(slot_id_hex: int) -> Any | None:
    """Request slot data from devnet node."""
    url = "https://rpc.fusaka-devnet-4.ethpandaops.io/"

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(slot_id_hex), True],  # True for full transaction objects
        "id": 1,
    }

    headers = {"Content-Type": "application/json"}

    try:
        # Make the request
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()

        # Return JSON response
        return response.json()

    except Exception as e:
        print(f"error: {e}")
        exit(1)


def extract_values_from_json_response(json_response, slot_id_hex: int) -> dict:
    """Extract blobSchedule and activation time data from the genesis JSON."""
    # get the blob schedules
    assert json_response is not None, "failed to read response: you passed 'None'"
    assert "result" in json_response, (
        f"failed to read response: 'config' field not found\nGot this response: {json_response}"
    )

    baseFeePerGas = json_response["result"]["baseFeePerGas"]  # noqa: N806
    blobGasUsed = json_response["result"]["blobGasUsed"]  # noqa: N806
    excessBlobGas = json_response["result"]["excessBlobGas"]  # noqa: N806
    timestamp = json_response["result"]["timestamp"]  # noqa: N806

    header_blob_values = {
        "baseFeePerGas": baseFeePerGas,
        "blobGasUsed": blobGasUsed,
        "excessBlobGas": excessBlobGas,
        "timestamp": timestamp,
        "blockId": slot_id_hex,
    }

    return header_blob_values


def main() -> None:  # noqa: D103
    slot_id_hex = 0xA000

    json_response = get_data_of_slot(slot_id_hex=slot_id_hex)
    header_blob_values = extract_values_from_json_response(
        json_response=json_response, slot_id_hex=slot_id_hex
    )  # type: ignore[annotation-unchecked]
    print(
        f"'baseFeePerGas':\t'{header_blob_values['baseFeePerGas']}'\n"
        f"'blobGasUsed':\t\t'{header_blob_values['blobGasUsed']}'\n"
        f"'excessBlobGas':\t'{header_blob_values['excessBlobGas']}'\n"
        f"'timestamp':\t\t'{header_blob_values['timestamp']}'\n"
        f"'blockId':\t\t'{header_blob_values['blockId']:#x}'\n"
    )


main()
