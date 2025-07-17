# Borrow timespan functions

import pandas as pd
import numpy as np
from .data_extraction import (
    collect_events_data,
    collect_prices_data,
    collect_reserves_data,
)
from .standardisation import (
    generate_days,
    rescaling_borrow,
    rescaling_repay,
    find_closest_price,
)
from datetime import datetime


def repayment(
    df_borrow_user,
    df_repay_user,
    first_repay=True,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_onBehalf="onBehalfOf",
    col_repayer="repayer",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
    col_price="underlyingTokenPriceUSD",
    col_event_price="underlyingEventPriceUSD",
):
    """
    Matches each borrowing transaction with either the first or the last repayment
    that cumulatively repays it, for a given user and asset.

    Parameters:
    -----------
    df_borrow_user : pd.DataFrame
        DataFrame containing borrow transactions for a specific user and asset.
    df_repay_user : pd.DataFrame
        DataFrame containing repayment transactions for the same user and asset.
    first_repay : bool
        If True, match with the first repayment exceeding the threshold;
        if False, match with the last one.
    col_amount : str
        Column name for the transaction amount.
    col_cumsum : str
        Column name for the cumulative transaction amount.
    col_user : str
        Column name identifying the user in the borrow DataFrame.
    col_asset : str
        Column name for the asset name (e.g., token).
    col_day : str
        Column name for the transaction date.
    col_block : str
        Column name for the block number.
    col_price : str
        Column name for the underlying token price in USD at borrowing.
    col_event_price : str
        Column name for the transaction price in USD at event time.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with borrow transactions enriched with the matched repayment info.
    """

    # Set prefix based on whether we are searching for the first or last repayment
    prefix = "First" if first_repay else "Last"

    # Handle empty repayment case by returning NaNs
    if df_repay_user.empty:
        return pd.DataFrame(
            {
                "user": df_borrow_user[col_onBehalf].values,
                "Reserve": df_borrow_user[col_asset].values,
                "Borrow_Day": df_borrow_user[col_day].values,
                "Borrow_blockNumber": df_borrow_user[col_block].values,
                "Borrow_Amount": df_borrow_user[col_amount].values,
                "Borrow_underlyingTokenPriceUSD": df_borrow_user[col_price].values,
                "Borrow_underlyingEventPriceUSD": df_borrow_user[
                    col_event_price
                ].values,
                f"{prefix}_Repayer": [pd.NaT] * len(df_borrow_user),
                f"{prefix}_Repay_Day": [pd.NaT] * len(df_borrow_user),
                f"{prefix}_Repay_blockNumber": [np.nan] * len(df_borrow_user),
                f"{prefix}_Repay_Amount": [np.nan] * len(df_borrow_user),
                f"{prefix}_Repay_underlyingTokenPriceUSD": [np.nan]
                * len(df_borrow_user),
                f"{prefix}_Repay_underlyingEventPriceUSD": [np.nan]
                * len(df_borrow_user),
                f"Time_to_{prefix}_Repay": [pd.NaT] * len(df_borrow_user),
            }
        )

    results = []

    # Extract repayment columns as NumPy arrays for efficiency
    repayer = df_repay_user[col_repayer].values
    repay_cumsum = df_repay_user[col_cumsum].values
    repay_day = df_repay_user[col_day].values
    repay_block = df_repay_user[col_block].values
    repay_amount = df_repay_user[col_amount].values
    repay_price = df_repay_user[col_price].values
    repay_event_price = df_repay_user[col_event_price].values

    # Extract borrow columns
    borrow_cumsum = df_borrow_user[col_cumsum].values
    borrow_amount = df_borrow_user[col_amount].values
    borrow_day = df_borrow_user[col_day].values
    borrow_block = df_borrow_user[col_block].values
    borrow_user = df_borrow_user[col_onBehalf].values
    borrow_asset = df_borrow_user[col_asset].values
    borrow_price = df_borrow_user[col_price].values
    borrow_event_price = df_borrow_user[col_event_price].values

    # Loop through each borrow transaction
    for i in range(len(df_borrow_user)):
        # Define the repayment threshold based on first/last setting
        threshold = (
            0
            if i == 0 and first_repay
            else borrow_cumsum[i - 1]
            if first_repay
            else borrow_cumsum[i]
        )

        # Search for the repayment that matches the threshold
        for j in range(len(df_repay_user)):
            if repay_block[j] >= borrow_block[i] and repay_cumsum[j] > threshold:
                # Match found: append enriched borrow-repay pair
                results.append(
                    {
                        "user": borrow_user[i],
                        "Reserve": borrow_asset[i],
                        "Borrow_Day": borrow_day[i],
                        "Borrow_blockNumber": borrow_block[i],
                        "Borrow_Amount": borrow_amount[i],
                        "Borrow_underlyingTokenPriceUSD": borrow_price[i],
                        "Borrow_underlyingEventPriceUSD": borrow_event_price[i],
                        f"{prefix}_Repayer": repayer[j],
                        f"{prefix}_Repay_Day": repay_day[j],
                        f"{prefix}_Repay_blockNumber": repay_block[j],
                        f"{prefix}_Repay_Amount": repay_amount[j],
                        f"{prefix}_Repay_underlyingTokenPriceUSD": repay_price[j],
                        f"{prefix}_Repay_underlyingEventPriceUSD": repay_event_price[j],
                        f"Time_to_{prefix}_Repay": pd.to_datetime(repay_day[j])
                        - pd.to_datetime(borrow_day[i]),
                    }
                )
                break  # Stop once the first match is found
        else:
            # No repayment match found: fill with NaNs
            results.append(
                {
                    "user": borrow_user[i],
                    "Reserve": borrow_asset[i],
                    "Borrow_Day": borrow_day[i],
                    "Borrow_blockNumber": borrow_block[i],
                    "Borrow_Amount": borrow_amount[i],
                    "Borrow_underlyingTokenPriceUSD": borrow_price[i],
                    "Borrow_underlyingEventPriceUSD": borrow_event_price[i],
                    f"{prefix}_Repayer": np.nan,
                    f"{prefix}_Repay_Day": pd.NaT,
                    f"{prefix}_Repay_blockNumber": np.nan,
                    f"{prefix}_Repay_Amount": np.nan,
                    f"{prefix}_Repay_underlyingTokenPriceUSD": np.nan,
                    f"{prefix}_Repay_underlyingEventPriceUSD": np.nan,
                    f"Time_to_{prefix}_Repay": pd.NaT,
                }
            )

    return pd.DataFrame(results)


def first_last_repayment(
    df_borrow_user,
    df_repay_user,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_onBehalf="onBehalfOf",
    col_repayer="repayer",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
    col_price="underlyingTokenPriceUSD",
    col_event_price="underlyingEventPriceUSD",
):
    """
    Combines the first and last repayment information for a set of borrow transactions.

    For each borrow, it retrieves:
    - The first repayment that begins to repay the loan using.
    - The last repayment that completes the repayment.

    Results are aligned by row index to allow horizontal concatenation.

    Parameters:
    -----------
    df_borrow_user : pd.DataFrame
        Borrow transactions for a given user and asset.
    df_repay_user : pd.DataFrame
        Corresponding repayment transactions.
    col_amount : str
        Column name for the transaction amount.
    col_cumsum : str
        Column name for the cumulative transaction amount.
    col_user : str
        Column name identifying the user in borrow data.
    col_asset : str
        Column name for the asset name.
    col_day : str
        Column name for the transaction date.
    col_block : str
        Column name for the block number.
    col_price : str
        Column for the token price at the time of borrow.
    col_event_price : str
        Column for the event-time price of the token.

    Returns:
    --------
    pd.DataFrame
        A DataFrame combining borrow transactions with both first and last repayment info.
    """

    # Compute first repayment info
    first_repay = repayment(
        df_borrow_user,
        df_repay_user,
        first_repay=True,
        col_amount=col_amount,
        col_cumsum=col_cumsum,
        col_onBehalf=col_onBehalf,
        col_repayer=col_repayer,
        col_asset=col_asset,
        col_day=col_day,
        col_block=col_block,
        col_price=col_price,
        col_event_price=col_event_price,
    )

    # Compute last repayment info
    last_repay = repayment(
        df_borrow_user,
        df_repay_user,
        first_repay=False,
        col_amount=col_amount,
        col_cumsum=col_cumsum,
        col_onBehalf=col_onBehalf,
        col_repayer=col_repayer,
        col_asset=col_asset,
        col_day=col_day,
        col_block=col_block,
        col_price=col_price,
        col_event_price=col_event_price,
    )

    # Define keys for merging both DataFrames
    merge_keys = [
        "user",
        "Reserve",
        "Borrow_Day",
        "Borrow_blockNumber",
        "Borrow_Amount",
        "Borrow_underlyingTokenPriceUSD",
        "Borrow_underlyingEventPriceUSD",
        "row_number",
    ]

    # Define columns from the last repayment to merge
    cols_last = [
        "Last_Repayer",
        "Last_Repay_Day",
        "Last_Repay_blockNumber",
        "Last_Repay_Amount",
        "Last_Repay_underlyingTokenPriceUSD",
        "Last_Repay_underlyingEventPriceUSD",
        "Time_to_Last_Repay",
    ]

    # Reset index to merge by row_number later
    first_repay = first_repay.reset_index(drop=True)
    last_repay = last_repay.reset_index(drop=True)

    # Add row number to merge on unique rows
    first_repay["row_number"] = first_repay.index
    last_repay["row_number"] = last_repay.index

    # Merge first and last repayment data
    df_repayment = first_repay.merge(
        last_repay[merge_keys + cols_last], on=merge_keys, how="inner"
    )

    # Security check to ensure row alignment
    assert len(df_repayment) == len(df_borrow_user)

    return df_repayment


def first_last_repayments_by_user(
    df_borrow,
    df_repay,
    user,
    col_amount="amount",
    col_user="user",
    col_onBehalf="onBehalfOf",
    col_repayer="repayer",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
    col_price="underlyingTokenPriceUSD",
    col_event_price="underlyingEventPriceUSD",
):
    """
    Computes first and last repayments for a specific user across all borrowed assets.

    Parameters:
    -----------
    df_borrow : pd.DataFrame
        Full borrow transaction dataset.
    df_repay : pd.DataFrame
        Full repayment transaction dataset.
    user : str
        The user identifier to filter the data.
    col_amount : str
        Column name for transaction amount.
    col_user_borrow : str
        Column name for the user in the borrow dataset.
    col_user_repay : str
        Column name for the user in the repayment dataset.
    col_asset : str
        Column name for the asset name.
    col_day : str
        Column name for transaction date.
    col_block : str
        Column name for the block number.
    col_price : str
        Column for the token price in USD.
    col_event_price : str
        Column for the price at event time in USD.

    Returns:
    --------
    pd.DataFrame
        Combined DataFrame with repayment info per borrow across assets for the given user.
    """

    # Filter borrow and repay data for the specified user
    borrow = df_borrow[
        (df_borrow[col_onBehalf] == user) & (df_borrow[col_user] == user)
    ].copy()
    repay = df_repay[(df_repay[col_user] == user)].copy()

    if borrow.empty:
        return
    # List unique borrowed assets
    assets = borrow[col_asset].unique()
    all_results = []

    # Iterate over all assets borrowed by the user
    for asset in assets:
        # Filter borrow transactions for that asset
        df_borrow_user = borrow[borrow[col_asset] == asset][
            [
                col_onBehalf,
                col_day,
                col_asset,
                col_amount,
                col_block,
                col_price,
                col_event_price,
            ]
        ].copy()
        # Compute cumulative borrowed amount
        df_borrow_user["Cumsum_amount"] = df_borrow_user[col_amount].cumsum()

        # Filter repayment transactions for that asset
        df_repay_user = repay[repay[col_asset] == asset][
            [
                col_user,
                col_repayer,
                col_day,
                col_asset,
                col_amount,
                col_block,
                col_price,
                col_event_price,
            ]
        ].copy()
        # Compute cumulative repaid amount
        df_repay_user["Cumsum_amount"] = df_repay_user[col_amount].cumsum()

        # Match borrow and repayment transactions
        df_repay_match = first_last_repayment(
            df_borrow_user,
            df_repay_user,
            col_amount,
            "Cumsum_amount",
            col_onBehalf,
            col_repayer,
            col_asset,
            col_day,
            col_block,
            col_price,
            col_event_price,
        )

        # Append result
        all_results.append(df_repay_match)

    # Concatenate all matched data across assets
    return pd.concat(all_results, axis=0, ignore_index=True)


def all_first_last_repayments(
    df_borrow,
    df_repay,
    col_amount="amount",
    col_user="user",
    col_user_borrow="onBehalfOf",
    col_repayer="repayer",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
    col_price="underlyingTokenPriceUSD",
    col_event_price="underlyingEventPriceUSD",
):
    """
    Computes first and last repayment matches for all users in the dataset.

    For each user:
    - Filters borrow and repayment transactions
    - Computes cumulative amounts
    - Matches each borrow with its first and last repayment
    - Aggregates the result across users

    Parameters:
    -----------
    df_borrow : pd.DataFrame
        Complete DataFrame of borrow transactions.
    df_repay : pd.DataFrame
        Complete DataFrame of repayment transactions.
    col_amount : str
        Column name for transaction amount.
    col_user_borrow : str
        Column name for borrower user.
    col_user_repay : str
        Column name for repayer user.
    col_asset : str
        Column name for the asset (e.g., token).
    col_day : str
        Column name for transaction day.
    col_block : str
        Column name for the block number.
    col_price : str
        Column for token price at time of transaction.
    col_event_price : str
        Column for price at event time.

    Returns:
    --------
    pd.DataFrame
        Concatenated DataFrame with repayment match info for all users and assets.
    """

    # List all unique users from borrow data
    users = df_borrow[col_user_borrow].unique()
    all_df = []

    # Process each user individually
    for i, user in enumerate(users, start=1):
        print(f"Processing user {i} out of {len(users)} : {user}")

        # Get repayment match for that user
        df_user = first_last_repayments_by_user(
            df_borrow,
            df_repay,
            user,
            col_amount=col_amount,
            col_user=col_user,
            col_onBehalf=col_user_borrow,
            col_repayer=col_repayer,
            col_asset=col_asset,
            col_day=col_day,
            col_block=col_block,
            col_price=col_price,
            col_event_price=col_event_price,
        )
        # Collect the result
        all_df.append(df_user)

    # Concatenate the results for all users
    df_all = pd.concat(all_df, axis=0, ignore_index=True)

    # Ensure block number columns remain integer-typed while allowing for missing values (NaN)
    for col in [
        "Borrow_blockNumber",
        "First_Repay_blockNumber",
        "Last_Repay_blockNumber",
    ]:
        df_all[col] = df_all[col].astype("Int64")

    return df_all


def collect_borrow_repay(start, stop):
    """
    Collects, merges and processes borrow and repay on-chain transactions
    for the AAVE protocol between two dates, assigning token prices based
    on the closest available price data at the block level.

    Parameters:
    -----------
    start : datetime
        Start date of the time period to collect data.
    stop : datetime
        End date of the time period to collect data.

    Returns:
    --------
    df_borrow_all : pd.DataFrame
        Cleaned and rescaled borrow transactions dataframe with prices attached.
    df_repay_all : pd.DataFrame
        Cleaned and rescaled repay transactions dataframe with prices attached.
    """

    # Initialize empty lists to store daily data
    borrow_list = []
    repay_list = []

    # Collect asset info for the whole period
    reserves = collect_reserves_data(start=start, stop=stop)

    # Convert token prices to match price scaling
    reserves["underlyingTokenPriceUSD"] *= 10**8

    # Loop through each day between start and stop
    for day in generate_days(start=start, stop=stop):
        # Collect daily borrow and repay transactions
        df_borrow = collect_events_data(event_type="borrow", start=day, stop=day)
        df_repay = collect_events_data(event_type="repay", start=day, stop=day)

        # Special case: skip price assignment for 2023-01-27, as the api does not have the value of prices data
        if day != datetime(2023, 1, 27):
            # Collect price data for the day
            prices = collect_prices_data(start=day, stop=day)

            # Process each asset separately
            for asset in prices["UnderlyingToken"].unique():
                # Filter prices for the asset
                prices_asset = prices[prices["UnderlyingToken"] == asset]

                # Ensure block numbers are integers and sorted
                prices_asset["BlockNumber"] = prices_asset["BlockNumber"].astype(int)
                block_numbers = np.sort(prices_asset["BlockNumber"].unique())

                # Create dictionary mapping block → price
                price_mapping = dict(
                    zip(prices_asset["BlockNumber"], prices_asset["Price"])
                )

                # Filter borrow transactions for the asset
                df_borrow_asset = df_borrow[df_borrow["reserve"] == asset]
                if not df_borrow_asset.empty:
                    # Assign closest price per row
                    df_borrow_asset["underlyingTokenPriceUSD"] = df_borrow_asset.apply(
                        lambda row: find_closest_price(
                            row, block_numbers, price_mapping
                        ),
                        axis=1,
                    )
                    borrow_list.append(df_borrow_asset)

                # Filter repay transactions for the asset
                df_repay_asset = df_repay[df_repay["reserve"] == asset]
                if not df_repay_asset.empty:
                    # Assign closest price per row
                    df_repay_asset["underlyingTokenPriceUSD"] = df_repay_asset.apply(
                        lambda row: find_closest_price(
                            row, block_numbers, price_mapping
                        ),
                        axis=1,
                    )
                    repay_list.append(df_repay_asset)

        else:
            # Fallback: store raw data without prices for Jan 27
            borrow_list.append(df_borrow)
            repay_list.append(df_repay)

    # Concatenate daily data into full DataFrames
    df_borrow_all = pd.concat(borrow_list, ignore_index=True)
    df_repay_all = pd.concat(repay_list, ignore_index=True)

    # Fill missing prices in df_borrow_all using reserve data as fallback
    df_borrow_all["underlyingTokenPriceUSD"] = df_borrow_all.apply(
        lambda row: reserves.loc[
            (reserves["underlyingAsset"] == row["reserve"])
            & (reserves["day"] == row["day"]),
            "underlyingTokenPriceUSD",
        ].iloc[0]
        if pd.isna(row["underlyingTokenPriceUSD"])
        and not reserves.loc[
            (reserves["underlyingAsset"] == row["reserve"])
            & (reserves["day"] == row["day"]),
            "underlyingTokenPriceUSD",
        ].empty
        else row["underlyingTokenPriceUSD"],
        axis=1,
    )

    # Merge reserve info (name, decimals) into df_borrow_all
    df_borrow_all = pd.merge(
        df_borrow_all,
        reserves[["day", "name", "decimals", "underlyingAsset"]],
        how="left",
        left_on=["reserve", "day"],
        right_on=["underlyingAsset", "day"],
    )

    # Merge reserve info (name, decimals) into df_repay_all
    df_repay_all = pd.merge(
        df_repay_all,
        reserves[["day", "name", "decimals", "underlyingAsset"]],
        how="left",
        left_on=["reserve", "day"],
        right_on=["underlyingAsset", "day"],
    )

    # Rescale the amounts
    df_borrow_all = rescaling_borrow(df_borrow_all)
    df_repay_all = rescaling_repay(df_repay_all)

    # np.nan in the df changed the type of blockNumber's column from int into float
    for col in [
        "Borrow_blockNumber",
        "First_Repay_blockNumber",
        "Last_Repay_blockNumber",
    ]:
        df_borrow_all[col] = df_borrow_all[col].astype("Int64")
        df_repay_all[col] = df_repay_all[col].astype("Int64")

    # Return cleaned and enriched datasets
    return df_borrow_all, df_repay_all
