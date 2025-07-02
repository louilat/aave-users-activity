import pandas as pd
import numpy as np
from pandas import DataFrame
import json
import requests
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


def collect_events_data(event_type: str, start: datetime, stop: datetime) -> DataFrame:
    """
    Collect the users events data from the api endpoint for a given time interval.
    Args:
        event_type (str): One of the following "borrow", "repay", "supply", "withdraw"
        start (datetime): The date at which the data collection starts.
        stop (datetime): The date at which the data collection stops (stop NOT included).
    Returns:
        DataFrame: The dataframe with the events data over the time interval.
    """
    events = DataFrame()
    day = start
    while day <= stop:
        print(f"Retrieving {event_type} data for {day}")
        month = day.ctime()[4:7]
        day_str = "-".join([day.strftime("%Y"), month, day.strftime("%d")])
        resp = requests.get(
            url=f"https://aavefulldata.lab.groupe-genes.fr/events/{event_type}",
            params={"date": day_str},
            verify=False,
        )
        day_events = pd.json_normalize(resp.json())
        day_events["day"] = day
        events = pd.concat((events, day_events))
        day += timedelta(days=1)
    return events.drop_duplicates()


def collect_reserves_data(start: datetime, stop: datetime) -> DataFrame:
    """
    Collect the pool-level data from the api endpoint for a given time interval.
    Args:
        start (datetime): The date at which the data collection starts.
        stop (datetime): The date at which the data collection stops (stop NOT included).
    Returns:
        DataFrame: The dataframe with the reserves data over the interval.
    """
    reserves = DataFrame()
    day = start
    while day <= stop:
        print(f"Retrieving reserves data for {day}")
        month = day.ctime()[4:7]
        day_str = "-".join([day.strftime("%Y"), month, day.strftime("%d")])
        resp = requests.get(
            url="https://aavefulldata.lab.groupe-genes.fr/reserves",
            params={"date": day_str},
            verify=False,
        )
        day_reserves = pd.json_normalize(resp.json())
        day_reserves["day"] = day
        reserves = pd.concat((reserves, day_reserves))
        day += timedelta(days=1)
    return reserves


def collect_prices_data(start: datetime, stop: datetime) -> DataFrame:
    """
    Collect the pool-level data from the api endpoint for a given time interval.
    Args:
        start (datetime): The date at which the data collection starts.
        stop (datetime): The date at which the data collection stops (stop NOT included).
    Returns:
        DataFrame: The dataframe with the ETH prices data over the interval.
    """
    prices = DataFrame()
    day = start
    while day <= stop:
        print(f"Retrieving prices data for {day}")
        month = day.ctime()[4:7]
        day_str = "-".join([day.strftime("%Y"), month, day.strftime("%d")])
        resp = requests.get(
            url="https://aavefulldata.lab.groupe-genes.fr/prices",
            params={"date": day_str},
            verify=False,
        )
        day_reserves = pd.json_normalize(resp.json())
        day_reserves["day"] = day
        prices = pd.concat((prices, day_reserves))
        day += timedelta(days=1)
    return prices


def get_user_transactions(alchemy_url, address, from_block, to_block, from_user=True):
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
        "category": ["erc20"],
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
    response = requests.post(alchemy_url, data=json.dumps(payload), headers=headers)

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

    # Format timestamp as datetime (remove timezone)
    tx["timestamp"] = pd.to_datetime(tx["timestamp"]).dt.tz_localize(None)

    # Convert hex fields to integers
    tx["blockNumber"] = tx["blockNumber"].apply(lambda x: int(x, 16))
    tx["decimals"] = tx["decimals"].apply(
        lambda x: int(x, 16) if pd.notnull(x) else np.nan
    )

    return tx


def extract_user_transactions(df, alchemy_url):
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
    tx = []
    all_sent = []
    all_received = []

    for row in df.itertuples(index=False):
        # Retrieve sent and received transactions
        tx_sent = get_user_transactions(
            alchemy_url=alchemy_url,
            address=row.user,
            from_block=row.Borrow_blockNumber,
            to_block=row.Last_Repay_blockNumber,
            from_user=True,
        )
        tx_received = get_user_transactions(
            alchemy_url=alchemy_url,
            address=row.user,
            from_block=row.Borrow_blockNumber,
            to_block=row.Last_Repay_blockNumber,
            from_user=False,
        )

        # Store user transactions along with metadata
        tx.append(
            {
                "user": row.user,
                "Borrowed_Asset": row.Reserve,
                "Borrow_Amount": row.Borrow_Amount,
                "Borrow_Amount_USD": row.Borrow_underlyingEventPriceUSD,
                "First_Repay_Amount": row.First_Repay_Amount,
                "First_Repay_blockNumber": row.First_Repay_blockNumber,
                "sent": tx_sent.to_dict(orient="records"),
                "received": tx_received.to_dict(orient="records"),
            }
        )

    # Flatten and enrich the transactions
    for entry in tx:
        for sent in entry["sent"]:
            sent.update(
                {
                    "user": entry["user"],
                    "Borrowed_Asset": entry["Borrowed_Asset"],
                    "Borrow_Amount": entry["Borrow_Amount"],
                    "Borrow_Amount_USD": entry["Borrow_Amount_USD"],
                    "First_Repay_Amount": entry["First_Repay_Amount"],
                    "First_Repay_blockNumber": entry["First_Repay_blockNumber"],
                    "direction": "sent",
                }
            )
            all_sent.append(sent)

        for received in entry["received"]:
            received.update(
                {
                    "user": entry["user"],
                    "Borrowed_Asset": entry["Borrowed_Asset"],
                    "Borrow_Amount": entry["Borrow_Amount"],
                    "Borrow_Amount_USD": entry["Borrow_Amount_USD"],
                    "First_Repay_Amount": entry["First_Repay_Amount"],
                    "First_Repay_blockNumber": entry["First_Repay_blockNumber"],
                    "direction": "received",
                }
            )
            all_received.append(received)

    # Create the final DataFrame
    df_tx = pd.DataFrame(all_sent + all_received)

    # Reorder columns to put key fields in front
    cols = df_tx.columns.tolist()
    for col in [
        "First_Repay_blockNumber",
        "First_Repay_Amount",
        "Borrow_Amount_USD",
        "Borrow_Amount",
        "Borrowed_Asset",
        "user",
    ]:
        if col in cols:
            cols.insert(0, cols.pop(cols.index(col)))
    df_tx = df_tx[cols]

    # Sort and clean
    df_tx.sort_values(by="blockNumber", inplace=True)
    df_tx = df_tx.dropna(subset=["asset"])

    return df_tx
