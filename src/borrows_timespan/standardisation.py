# map the token
import pandas as pd
from datetime import timedelta
import numpy as np
from web3 import Web3
from hexbytes import HexBytes


def generate_days(start, stop):
    """
    Generate a list of dates between start_date and end_date (included).

    Arguments:
    start_date (datetime.date or datetime64): Start date.
    end_date (datetime.date or datetime64): End date.

    Returns:
    list: List of dates from start_date to end_date.
    """
    delta = (stop - start).days
    return [start + timedelta(days=i) for i in range(delta + 1)]


def find_closest_price(row, block_numbers, price_mapping):
    """
    For a given event (row), find the price corresponding to the closest block in the prices DataFrame.

    Arguments:
    row (pandas.Series): A row from df_borrow containing 'blockNumber' and 'reserve'.
    block_numbers (np.ndarray): Array of block numbers from the prices DataFrame
    price_mapping (dict): Dictionary mapping block numbers to token prices.

    Returns:
    float: The price corresponding to the closest block.
    """
    # If the array of known block numbers is empty, return NaN
    if block_numbers.size == 0:
        return np.nan

    # Compute the absolute difference between current block and all known block numbers
    delta = np.abs(block_numbers - np.int64(row["blockNumber"]))
    # Find the index of the closest block
    idx = np.argmin(delta)
    # Get the actual closest block number
    closest_block = block_numbers[idx]

    # Return the price corresponding to the closest block, or NaN if not found
    return price_mapping.get(closest_block, np.nan)


def rescaling_borrow(
    df_borrow,
    col_amount="amount",
    col_decimals="decimals",
    col_price="underlyingTokenPriceUSD",
    col_event_price="underlyingEventPriceUSD",
    col_block="blockNumber",
    col_asset="reserve",
    col_name="name",
    col_user_borrow="onBehalfOf",
    col_user="user",
    col_day="day",
):
    """
    Function that rescale the amounts of borrow events.

    Parameters:
    -----------
    df_borrow : pd.DataFrame
        Borrowing transactions.

    col_amount : str
        Column name for the raw borrowed amount.
    col_decimals : str
        Column name for the token decimals.
    col_price : str
        Column name for the token price in USD (scaled by 1e8).
    col_event_price : str
        Column name where the USD value of the event will be stored.
    col_block : str
        Column name for the block number.
    col_asset : str
        Column name for the asset identifier.
    col_name : str
        Column name for the token name to be renamed as 'reserve_name'.
    col_user_borrow : str
        Column name for the effective borrower (onBehalfOf).
    col_user : str
        Column name for the initiator of the transaction.
    col_day : str
        Column name for the transaction date.

    Returns:
    --------
    pd.DataFrame
        Dataframe of borrows in which the values of the transactions are correctly rescaled and the column reordered.
    """

    # Rescale the values of transactions
    df_borrow[col_amount] = (
        (df_borrow[col_amount] / (10 ** df_borrow[col_decimals])).astype(float).round(6)
    )

    df_borrow[col_price] = ((df_borrow[col_price] / 10**8).astype(float)).round(6)

    df_borrow[col_event_price] = df_borrow[col_price] * df_borrow[col_amount]

    # Reorder columns after ther merge
    new_order_borrow = [
        col_block,
        col_asset,
        col_name,
        col_decimals,
        col_user_borrow,
        col_user,
        col_amount,
        col_event_price,
        col_price,
        col_day,
    ]
    df_borrow = df_borrow[new_order_borrow]

    # Ensure that amount is float64
    df_borrow[col_amount] = df_borrow[col_amount].astype("float64")

    # Group by unique borrow identifiers and sum amounts in case of duplicates
    df_borrow = df_borrow.groupby(
        [
            col_block,
            col_asset,
            col_name,
            col_decimals,
            col_user_borrow,
            col_user,
            col_event_price,
            col_price,
            col_day,
        ],
        as_index=False,
    ).sum({col_amount: "sum"})

    # Rename 'name' to 'reserve_name' for consistency with repayment table
    df_borrow = df_borrow.rename(columns={col_name: "reserve_name"})
    return df_borrow


def rescaling_repay(
    df_repay,
    col_amount="amount",
    col_decimals="decimals",
    col_price="underlyingTokenPriceUSD",
    col_event_price="underlyingEventPriceUSD",
    col_block="blockNumber",
    col_asset="reserve",
    col_name="name",
    col_user="user",
    col_repayer="repayer",
    col_use_a_tokens="useATokens",
    col_day="day",
):
    """
    Function that rescale the amounts of repay events.

    Parameters:
    -----------
    df_repay : pd.DataFrame
        Repayment transactions.

    col_amount : str
        Column name for the raw repaid amount.
    col_decimals : str
        Column name for the token decimals.
    col_price : str
        Column name for the token price in USD (scaled by 1e8).
    col_event_price : str
        Column name where the USD value of the event will be stored.
    col_block : str
        Column name for the block number.
    col_asset : str
        Column name for the asset identifier.
    col_name : str
        Column name for the token name to be renamed as 'reserve_name'.
    col_user : str
        Column name for the user whose debt is being repaid.
    col_repayer : str
        Column name for the account executing the repayment.
    col_use_a_tokens : str
        Column name indicating whether the repayment used aTokens.
    col_day : str
        Column name for the transaction date.

    Returns:
    --------
    pd.DataFrame
        Dataframe of repayments in which the values of the transactions are correctly rescaled and the column reordered.
    """

    # Rescale the values of transactions
    df_repay[col_amount] = (
        (df_repay[col_amount] / (10 ** df_repay[col_decimals])).astype(float).round(6)
    )

    df_repay[col_price] = (df_repay[col_price] / 10**8).astype(float).round(6)

    # Calculate the USD price of the repay
    df_repay[col_event_price] = df_repay[col_price] * df_repay[col_amount]

    # Reorder columns
    new_order_repay = [
        col_block,
        col_asset,
        col_name,
        col_decimals,
        col_user,
        col_repayer,
        col_amount,
        col_event_price,
        col_price,
        col_use_a_tokens,
        col_day,
    ]
    df_repay = df_repay[new_order_repay]

    # Ensure that amount is float64
    df_repay[col_amount] = df_repay[col_amount].astype("float64")

    # Group by unique borrow identifiers and sum amounts in case of duplicates
    df_repay = df_repay.groupby(
        [
            col_block,
            col_asset,
            col_name,
            col_decimals,
            col_user,
            col_repayer,
            col_event_price,
            col_price,
            col_day,
        ],
        as_index=False,
    ).sum({col_amount: "sum"})

    # Rename 'name' to 'reserve_name' for consistency with repayment table
    df_repay = df_repay.rename(columns={col_name: "reserve_name"})

    return df_repay


def add_timestamp(
    df,
    blocksTimestamps,
    mode="r",
    col_timestamp="timestamp",
    col_blockNumber_timestamp="blockNumber",
    col_blockNumber_borrow=None,
    col_blockNumber_first=None,
    col_blockNumber_last=None,
    col_day_borrow=None,
    col_day_first=None,
    col_day_last=None,
):
    """
    Adds timestamp columns to a given DataFrame by mapping block numbers to corresponding timestamps.
    Each mapping is optional and only applied if the corresponding column arguments are provided.

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame containing columns of block numbers to be mapped.
    blocksTimestamps : str, optional
        Path to the JSON file containing the block numbers and their corresponding timestamps.
    mode : str, optional
        File opening mode for reading the JSON file.
    col_timestamp : str, optional
        Name of the timestamp field in the JSON file.
    col_blockNumber_timestamp : str, optional
        Name of the blockNumber field in the JSON file.
    col_blockNumber_borrow : str, optional
        Column name in df containing borrow block numbers.
    col_blockNumber_first : str, optional
        Column name in df containing first repay block numbers.
    col_blockNumber_last : str, optional
        Column name in df containing last repay block numbers.
    col_day_borrow : str, optional
        Name of the output column for borrow timestamps.
    col_day_first : str, optional
        Name of the output column for first repay timestamps.
    col_day_last : str, optional
        Name of the output column for last repay timestamps.

    Returns:
    --------
    df : pd.DataFrame
        The input DataFrame with the new timestamp columns added where specified.
    """
    # Convert Unix timestamps to pandas datetime
    blocksTimestamps[col_timestamp] = pd.to_datetime(
        blocksTimestamps[col_timestamp], unit="s"
    )

    # Build dictionary: blockNumber -> timestamp
    block_to_timestamp = dict(
        zip(
            blocksTimestamps[col_blockNumber_timestamp], blocksTimestamps[col_timestamp]
        )
    )

    # Apply mapping for borrow if column specified
    if col_blockNumber_borrow and col_day_borrow:
        df[col_day_borrow] = df[col_blockNumber_borrow].map(block_to_timestamp)

    # Apply mapping for first repayment if column specified
    if col_blockNumber_first and col_day_first:
        df[col_day_first] = df[col_blockNumber_first].map(block_to_timestamp)
        df["Time_to_First_Repay"] = df[col_day_first] - df[col_day_borrow]
    # Apply mapping for last repayment if column specified
    if col_blockNumber_last and col_day_last:
        df[col_day_last] = df[col_blockNumber_last].map(block_to_timestamp)
        df["Time_to_Last_Repay"] = df[col_day_last] - df[col_day_borrow]

    return df


def classify_addresses(df, alchemy_api_key):
    """
    Classify addresses in a transaction DataFrame as either 'Address', 'Contract', or 'Unknown'.

    This function:
    - Creates a new 'address' column depending on the transaction direction ('sent' or 'received').
    - Queries the Ethereum blockchain to determine if each unique address is an EOA or a contract.
    - Assigns the result to a 'type' column.

    Args:
        df (pd.DataFrame): The transaction DataFrame, must have 'from', 'to', and 'direction' columns.
        alchemy_api_key (str): Your Alchemy API key.

    Returns:
        pd.DataFrame: The input DataFrame with added 'address' and 'type' columns.
    """
    alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    w3 = Web3(Web3.HTTPProvider(alchemy_url))

    # Treatment of the case of the null address
    zero_address = "0x0000000000000000000000000000000000000000"

    # Replace 'from' if equal to zero address
    df.loc[df["from"] == zero_address, "from"] = df.loc[
        df["from"] == zero_address, "reserve"
    ]

    # Replace 'to' if equal to zero address
    df.loc[df["to"] == zero_address, "to"] = df.loc[df["to"] == zero_address, "reserve"]

    # Create the 'address' column based on direction
    df["address"] = df.apply(
        lambda row: row["to"] if row["direction"] == "sent" else row["from"], axis=1
    )

    # Build mapping of unique addresses to their type
    address_types = {}
    unique_addresses = df["address"].astype(str).unique()

    for addr in unique_addresses:
        try:
            checksum_addr = w3.to_checksum_address(addr)
            code = w3.eth.get_code(checksum_addr)
            if code == HexBytes("0x"):
                address_types[addr] = "Address"
            else:
                address_types[addr] = "Contract"
        except Exception as e:
            print(f"Error with address {addr}: {e}")
            address_types[addr] = "Unknown"

    # Map the classification back to the DataFrame
    df["type"] = df["address"].map(address_types)

    return df


def fetch_erc20_metadata(df, alchemy_api_key):
    """
    Fetches ERC20 token metadata (symbol and name) for all contract addresses in a DataFrame.

    This function:
    - Initializes a Web3 instance from the provided Alchemy API key.
    - Identifies unique contract addresses from the 'address' column where type == 'Contract'.
    - Tries to query the ERC20 symbol and name using the standard string ABI.
    - Falls back to the bytes32 ABI if needed.
    - Maps the results back to the DataFrame in a 'contract_name' column.

    Args:
        df (pd.DataFrame): DataFrame with columns 'address' and 'type'.
        alchemy_api_key (str): Your Alchemy API key.

    Returns:
        pd.DataFrame: The input DataFrame with an added 'contract_name' column.
    """
    ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function",
        },
    ]

    ERC20_ABI_BYTES32 = [
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "bytes32"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "bytes32"}],
            "type": "function",
        },
    ]

    unique_addresses = df[df["type"] == "Contract"]["address"].dropna().unique()

    token_metadata = {}

    for addr in unique_addresses:
        try:
            addr_checksum = w3.to_checksum_address(addr)

            # Skip if no bytecode (not really a contract)
            if w3.eth.get_code(addr_checksum) == b"":
                print(f"Skipping {addr} (no bytecode)")
                continue

            # Try standard ABI first
            try:
                contract = w3.eth.contract(address=addr_checksum, abi=ERC20_ABI)
                symbol = contract.functions.symbol().call()
                name = contract.functions.name().call()

            except Exception:
                # Fallback to bytes32 ABI
                contract_bytes32 = w3.eth.contract(
                    address=addr_checksum, abi=ERC20_ABI_BYTES32
                )
                symbol = contract_bytes32.functions.symbol().call()
                name = contract_bytes32.functions.name().call()

                # Decode bytes32 fields
                if isinstance(symbol, bytes):
                    symbol = symbol.decode("utf-8", errors="ignore").rstrip("\x00")
                if isinstance(name, bytes):
                    name = name.decode("utf-8", errors="ignore").rstrip("\x00")

            token_metadata[addr] = f"{name} ({symbol})"

        except Exception as e:
            token_metadata[addr] = np.nan
            print(f"Could not fetch ERC20 metadata for {addr}: {e}")

    # Map metadata to DataFrame
    df["contract_name"] = df["address"].map(token_metadata)

    return df
