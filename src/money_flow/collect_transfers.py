import time
import json
import requests
import pandas as pd
import numpy as np


def get_user_transactions(
    alchemy_api_key, address, from_block, to_block, from_user=True
):
    """
    Retrieves and processes all asset transfers received by an address between two block numbers.

    Parameters:
    -----------
    address : str
        Ethereum address to track.
    from_block : int
        Start block number (inclusive).
    to_block : int
        End block number (inclusive).
    from_user : bool
        Determine whether we collect the transactions sent or received

    Returns:
    --------
    pd.DataFrame
        Cleaned and formatted DataFrame of received asset transfers.
    """
    # Build base params dict
    params_dict = {
        "fromBlock": hex(from_block),
        "toBlock": hex(to_block),
        "category": ["erc20", "internal", "external"],
        "withMetadata": True,
        "maxCount": "0x3e8",
    }

    # Specify fromAddress or toAddress in the params dict
    if from_user:
        params_dict["fromAddress"] = address.lower()
    else:
        params_dict["toAddress"] = address.lower()

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [params_dict],
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}",
        data=json.dumps(payload),
        headers=headers,
    )

    if not response.ok:
        print(f"Error for {address}: {response.status_code}")
        return pd.DataFrame()

    # Define columns
    columns = [
        "uniqueId",
        "hash",
        "blockNum",
        "from",
        "to",
        "rawContract.address",
        "asset",
        "value",
        "rawContract.decimal",
        "category",
        "metadata.blockTimestamp",
    ]

    # Normalize JSON response into flat DataFrame
    tx = pd.json_normalize(response.json()["result"]["transfers"])[columns]

    # Rename relevant columns
    tx.rename(
        columns={
            "hash": "tx_hash",
            "uniqueId": "event_id",
            "blockNum": "blockNumber",
            "metadata.blockTimestamp": "timestamp",
            "rawContract.decimal": "decimals",
            "rawContract.address": "reserve",
        },
        inplace=True,
    )

    return tx


def extract_user_transactions(df, alchemy_api_key):
    """
    Extracts and enriches sent and received transactions for a list of users.

    Args:
        df (pd.DataFrame): A DataFrame containing the following columns:
            - user
            - Reserve
            - Borrow_Amount
            - Borrow_underlyingEventPriceUSD
            - First_Repay_Amount
            - Borrow_blockNumber
            - First_Repay_blockNumber

    Returns:
        pd.DataFrame: A combined DataFrame with enriched transactions sorted by block number.
    """
    all_sent = []
    all_received = []

    for row in df.itertuples(index=False):
        # Retrieve sent and received transactions
        tx_sent = get_user_transactions(
            alchemy_api_key,
            address=row.user,
            from_block=row.Borrow_blockNumber,
            to_block=row.Last_Repay_blockNumber,
            from_user=True,
        )

        time.sleep(0.3)

        tx_received = get_user_transactions(
            alchemy_api_key,
            address=row.user,
            from_block=row.Borrow_blockNumber,
            to_block=row.Last_Repay_blockNumber,
            from_user=False,
        )
        # Enrich sent transactions
        sent_records = tx_sent.to_dict(orient="records")
        for sent in sent_records:
            sent.update(
                {
                    "user": row.user,
                    "Borrowed_Asset": row.Reserve,
                    "Borrow_Amount": row.Borrow_Amount,
                    "Borrow_Amount_USD": row.Borrow_underlyingEventPriceUSD,
                    "Last_Repay_Amount": row.Last_Repay_Amount,
                    "Last_Repay_blockNumber": row.Last_Repay_blockNumber,
                    "direction": "sent",
                }
            )
            all_sent.append(sent)

        # Enrich received transactions
        received_records = tx_received.to_dict(orient="records")
        for received in received_records:
            received.update(
                {
                    "user": row.user,
                    "Borrowed_Asset": row.Reserve,
                    "Borrow_Amount": row.Borrow_Amount,
                    "Borrow_Amount_USD": row.Borrow_underlyingEventPriceUSD,
                    "Last_Repay_Amount": row.Last_Repay_Amount,
                    "Last_Repay_blockNumber": row.Last_Repay_blockNumber,
                    "direction": "received",
                }
            )
            all_received.append(received)

    # Create the final DataFrame
    df_tx = pd.DataFrame(all_sent + all_received)

    # Format timestamp as datetime (remove timezone)
    df_tx["timestamp"] = pd.to_datetime(df_tx["timestamp"]).dt.tz_localize(None)

    # Convert hex fields to integers
    df_tx["blockNumber"] = df_tx["blockNumber"].apply(lambda x: int(x, 16))
    df_tx["decimals"] = df_tx["decimals"].apply(
        lambda x: int(x, 16) if pd.notnull(x) else np.nan
    )

    # Reorder columns to put key fields in front
    cols = [
        "user",
        "Borrowed_Asset",
        "Borrow_Amount",
        "Borrow_Amount_USD",
        "Last_Repay_Amount",
        "Last_Repay_blockNumber",
        "event_id",
        "tx_hash",
        "blockNumber",
        "from",
        "to",
        "reserve",
        "asset",
        "value",
        "decimals",
        "category",
        "timestamp",
        "direction",
    ]
    df_tx = df_tx[cols]

    # Sort and clean
    df_tx.sort_values(by="blockNumber", inplace=True)
    df_tx = df_tx.dropna(subset=["asset"])

    return df_tx
