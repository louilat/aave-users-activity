# map the token
import pandas as pd
from datetime import timedelta
import numpy as np
import json


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
    Function that merge the dataframe of borrows and of reserves to get the underlying price in USD and the decimals
    necessary to rescale the amounts.

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
    df_borrow[col_amount].astype("float64")

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
    Function that merge the dataframe of borrows and of reserves to get the underlying price in USD and the decimals
    necessary to rescale the amounts.

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
    df_repay = df_repay[col_amount].astype("float64")

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
    blocksTimestamps="blocksTimestamps.json",
    mode="r",
    col_timestamp="timestamp",
    col_blockNumber_timestamp="blockNumber",
    col_blockNumber_df_borrow=None,
    col_blockNumber_df_first=None,
    col_blockNumber_df_last=None,
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
    col_blockNumber_df_borrow : str, optional
        Column name in df containing borrow block numbers.
    col_blockNumber_df_first : str, optional
        Column name in df containing first repay block numbers.
    col_blockNumber_df_last : str, optional
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

    # Load JSON containing block -> timestamp mapping
    with open(blocksTimestamps, mode) as file:
        blocksTimestamps = json.load(file)

    # Convert JSON to DataFrame
    blocksTimestamps = pd.DataFrame(blocksTimestamps)

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
    if col_blockNumber_df_borrow and col_day_borrow:
        df[col_day_borrow] = df[col_blockNumber_df_borrow].map(block_to_timestamp)

    # Apply mapping for first repayment if column specified
    if col_blockNumber_df_first and col_day_first:
        df[col_day_first] = df[col_blockNumber_df_first].map(block_to_timestamp)
        df["Time_to_First_Repay"] = df[col_day_first] - df[col_day_borrow]
    # Apply mapping for last repayment if column specified
    if col_blockNumber_df_last and col_day_last:
        df[col_day_last] = df[col_blockNumber_df_last].map(block_to_timestamp)
        df["Time_to_Last_Repay"] = df[col_day_last] - df[col_day_borrow]

    return df
