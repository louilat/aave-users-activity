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


def get_user_transactions_sent(ALCHEMY_URL, address, from_block, to_block):
    """
    Retrieves and processes all asset transfers sent from an address between two block numbers.

    Parameters:
    -----------
    address : str
        Ethereum address to track.
    from_block : int
        Start block number (inclusive).
    to_block : int
        End block number (inclusive).

    Returns:
    --------
    pd.DataFrame
        Cleaned and formatted DataFrame of sent asset transfers.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "fromAddress": address.lower(),  # Sent only
                "category": ["erc20"],
                "withMetadata": True,
                "maxCount": "0x3e8",
            }
        ],
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(ALCHEMY_URL, data=json.dumps(payload), headers=headers)

    if not response.ok:
        print(f"Error (sent) for {address}: {response.status_code}")
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
    tx_sent = pd.json_normalize(response.json()["result"]["transfers"])[columns]

    # Rename relevant columns
    tx_sent.rename(
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
    tx_sent["timestamp"] = pd.to_datetime(tx_sent["timestamp"]).dt.tz_localize(None)

    # Convert hex fields to integers
    tx_sent["blockNumber"] = tx_sent["blockNumber"].apply(lambda x: int(x, 16))
    tx_sent["decimals"] = tx_sent["decimals"].apply(
        lambda x: int(x, 16) if pd.notnull(x) else np.nan
    )

    return tx_sent


def get_user_transactions_received(ALCHEMY_URL, address, from_block, to_block):
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

    Returns:
    --------
    pd.DataFrame
        Cleaned and formatted DataFrame of received asset transfers.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "toAddress": address.lower(),  # Received only
                "category": ["erc20"],
                "withMetadata": True,
                "maxCount": "0x3e8",
            }
        ],
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(ALCHEMY_URL, data=json.dumps(payload), headers=headers)

    if not response.ok:
        print(f"Error (received) for {address}: {response.status_code}")
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
    tx_received = pd.json_normalize(response.json()["result"]["transfers"])[columns]

    # Rename relevant columns
    tx_received.rename(
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
    tx_received["timestamp"] = pd.to_datetime(tx_received["timestamp"]).dt.tz_localize(
        None
    )

    # Convert hex fields to integers
    tx_received["blockNumber"] = tx_received["blockNumber"].apply(lambda x: int(x, 16))
    tx_received["decimals"] = tx_received["decimals"].apply(
        lambda x: int(x, 16) if pd.notnull(x) else np.nan
    )

    return tx_received
