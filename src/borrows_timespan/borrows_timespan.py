# Borrow timespan functions

import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def first_repayment(
    df_borrow_user,
    df_repay_user,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_user="onBehalfOf",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
):
    """
    Match each borrowing transaction with the first 'observed' repayment transaction
    from the same user and asset that occurs after it, regardless of whether
    it fully covers the borrowed amount.

    Parameters:
    -----------
    df_borrow_user : pd.DataFrame
        Borrowing transactions filtered for one user and one asset.
    df_repay_user : pd.DataFrame
        Repayment transactions filtered for the same user and asset.
    col_amount : float
        Name of the column representing the transaction amount.
    col_cumsum : float
        Name of the column with the cumulative sum of the amounts.
    col_user : str
        Name of the column identifying the user/wallet.
    col_asset : str
        Name of the column identifying the asset/token.
    col_day : pd.DateTime
        Name of the column with the transaction date.
    col_block : str
        Name of the column with the block number.

    Returns:
    --------
    pd.DataFrame
        One row per borrow transaction, enriched with the first observed repayment info.
    """
    if df_repay_user.empty:
        return pd.DataFrame(
            {
                "user": df_borrow_user[col_user].values,
                "Reserve": df_borrow_user[col_asset].values,
                "Borrow_Day": df_borrow_user[col_day].values,
                "Borrow_blockNumber": df_borrow_user[col_block].values,
                "Borrow_Amount": df_borrow_user[col_amount].values,
                "First_Repay_Day": pd.NaT,
                "First_Repay_blockNumber": np.nan,
                "First_Repay_Amount": np.nan,
                "Time_to_First_Repay": pd.NaT,
            }
        )

    results = []
    # Special case: if only one repayment exists, assign it to all borrowings
    if len(df_repay_user) == 1:
        repay = df_repay_user.iloc[0]
        for i in range(len(df_borrow_user)):
            if (
                repay[col_day] >= df_borrow_user.iloc[i][col_day]
            ):  # ensure repayment is after borrow
                results.append(
                    {
                        "user": df_borrow_user.iloc[i][col_user],
                        "Reserve": df_borrow_user.iloc[i][col_asset],
                        "Borrow_Day": df_borrow_user.iloc[i][col_day],
                        "Borrow_blockNumber": df_borrow_user.iloc[i][col_block],
                        "Borrow_Amount": df_borrow_user.iloc[i][col_amount],
                        "First_Repay_Day": repay[col_day],
                        "First_Repay_blockNumber": repay[col_block],
                        "First_Repay_Amount": repay[col_amount],
                        "Time_to_First_Repay": repay[col_day]
                        - df_borrow_user.iloc[i][col_day],
                    }
                )
            else:
                results.append(
                    {
                        "user": df_borrow_user.iloc[i][col_user],
                        "Reserve": df_borrow_user.iloc[i][col_asset],
                        "Borrow_Day": df_borrow_user.iloc[i][col_day],
                        "Borrow_blockNumber": df_borrow_user.iloc[i][col_block],
                        "Borrow_Amount": df_borrow_user.iloc[i][col_amount],
                        "First_Repay_Day": pd.NaT,
                        "First_Repay_blockNumber": np.nan,
                        "First_Repay_Amount": np.nan,
                        "Time_to_First_Repay": pd.NaT,
                    }
                )
        return pd.DataFrame(results)

    # General case
    repay_len = len(df_repay_user)

    # Extract repayment data as numpy arrays (performance optimization)
    repay_cumsum = df_repay_user[col_cumsum].values
    repay_day = df_repay_user[col_day].values
    repay_block = df_repay_user[col_block].values
    repay_amount = df_repay_user[col_amount].values

    # Extract borrowing data
    borrow_cumsum = df_borrow_user[col_cumsum].values
    borrow_amount = df_borrow_user[col_amount].values
    borrow_day = df_borrow_user[col_day].values
    borrow_block = df_borrow_user[col_block].values
    borrow_user = df_borrow_user[col_user].values
    borrow_asset = df_borrow_user[col_asset].values

    # Iterate through each borrow transaction
    for i in range(len(df_borrow_user)):
        matched = False
        index_repay = 0
        # Loop through repayments to find the first valid one
        while not matched and index_repay < repay_len:
            repay_cum = repay_cumsum[index_repay]

            # Skip repayments occurring before the borrow date
            if repay_day[index_repay] >= borrow_day[i]:
                # Special case: first borrow transaction
                if i == 0:
                    # We match the first repayment whose cumulative value is less than the borrow
                    if borrow_amount[i] >= repay_cum:
                        results.append(
                            {
                                "user": borrow_user[i],
                                "Reserve": borrow_asset[i],
                                "Borrow_Day": borrow_day[i],
                                "Borrow_blockNumber": borrow_block[i],
                                "Borrow_Amount": borrow_amount[i],
                                "First_Repay_Day": repay_day[index_repay],
                                "First_Repay_blockNumber": repay_block[index_repay],
                                "First_Repay_Amount": repay_amount[index_repay],
                                "Time_to_First_Repay": repay_day[index_repay]
                                - borrow_day[i],
                            }
                        )
                        matched = True
                    else:
                        index_repay += 1

                # General case: later borrow transactions
                else:
                    delta = repay_cum - borrow_cumsum[i - 1]

                    # If the repayment occurred *after* the previous borrow (in cumulative terms)
                    if delta > 0:
                        results.append(
                            {
                                "user": borrow_user[i],
                                "Reserve": borrow_asset[i],
                                "Borrow_Day": borrow_day[i],
                                "Borrow_blockNumber": borrow_block[i],
                                "Borrow_Amount": borrow_amount[i],
                                "First_Repay_Day": repay_day[index_repay],
                                "First_Repay_blockNumber": repay_block[index_repay],
                                "First_Repay_Amount": repay_amount[index_repay],
                                "Time_to_First_Repay": repay_day[index_repay]
                                - borrow_day[i],
                            }
                        )
                        matched = True
                    else:
                        index_repay += 1

            else:
                index_repay += 1
        if not matched:
            results.append(
                {
                    "user": borrow_user[i],
                    "Reserve": borrow_asset[i],
                    "Borrow_Day": borrow_day[i],
                    "Borrow_blockNumber": borrow_block[i],
                    "Borrow_Amount": borrow_amount[i],
                    "First_Repay_Day": pd.NaT,
                    "First_Repay_blockNumber": np.nan,
                    "First_Repay_Amount": np.nan,
                    "Time_to_First_Repay": pd.NaT,
                }
            )

    return pd.DataFrame(results)


def last_repayment(
    df_borrow_user,
    df_repay_user,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_user="onBehalfOf",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
):
    """
    Match each borrowing transaction with the first repayment transaction that
    cumulatively repays it, for the same user and reserve (asset).

    This generalized version accepts flexible column names as arguments so it can be reused
    across different datasets with similar structure but different field names.

    Parameters:
        df_borrow_user (DataFrame): Filtered borrowing transactions for a specific user.
        df_repay_user (DataFrame): Filtered repayment transactions for the same user.
        col_amount (str): Column name for the transaction amount.
        col_cumsum (str): Column name for the cumulative sum of repayments.
        col_user (str): Column name for the user address.
        col_asset (str): Column name for the token/reserve name.
        col_day (str): Column name for the transaction day or timestamp.
        col_block (str): Column name for the block number.

    Returns:
        pd.DataFrame: A table where each row maps a borrow to its corresponding covering repayment.
    """
    if df_repay_user.empty:
        return pd.DataFrame(
            {
                "user": df_borrow_user[col_user].values,
                "Reserve": df_borrow_user[col_asset].values,
                "Borrow_Day": df_borrow_user[col_day].values,
                "Borrow_blockNumber": df_borrow_user[col_block].values,
                "Borrow_Amount": df_borrow_user[col_amount].values,
                "Last_Repay_Day": pd.NaT,
                "Last_Repay_blockNumber": np.nan,
                "Last_Repay_Amount": np.nan,
                "Time_to_Last_Repay": pd.NaT,
            }
        )

    # List to store matched repayment entries
    results = []

    # Repayment index tracker
    index_repay = 0
    repay_len = len(df_repay_user)

    # Extract repayment data as arrays for fast access
    repay_cumsum = df_repay_user[col_cumsum].values
    repay_day = df_repay_user[col_day].values
    repay_block = df_repay_user[col_block].values
    repay_amount = df_repay_user[col_amount].values

    # Extract borrowing data as arrays
    borrow_cumsum = df_borrow_user[col_cumsum].values
    borrow_amount = df_borrow_user[col_amount].values
    borrow_day = df_borrow_user[col_day].values
    borrow_block = df_borrow_user[col_block].values
    borrow_user = df_borrow_user[col_user].values
    borrow_asset = df_borrow_user[col_asset].values

    # Iterate over borrow transactions
    for i in range(len(df_borrow_user)):
        matched = False  # Flag to indicate if a repayment was found

        # Look for the first repayment that fully covers the borrow
        while not matched and index_repay < repay_len:
            repay_cum = repay_cumsum[index_repay]

            # Define the threshold to repay depending on borrow index
            threshold = (
                borrow_amount[i] if i == 0 else borrow_amount[i] + borrow_cumsum[i - 1]
            )

            # Check if cumulative repayment is sufficient
            if repay_cum >= threshold:
                # Record the match
                results.append(
                    {
                        "user": borrow_user[i],
                        "Reserve": borrow_asset[i],
                        "Borrow_Day": borrow_day[i],
                        "Borrow_blockNumber": borrow_block[i],
                        "Borrow_Amount": borrow_amount[i],
                        "Last_Repay_Day": repay_day[index_repay],
                        "Last_Repay_blockNumber": repay_block[index_repay],
                        "Last_Repay_Amount": repay_amount[index_repay],
                        "Time_to_Last_Repay": repay_day[index_repay] - borrow_day[i],
                    }
                )
                matched = True
            else:
                # Move to the next repayment if not yet covered
                index_repay += 1

    if not results:
        # No last repayment matched any borrow
        return pd.DataFrame(
            {
                "user": borrow_user,
                "Reserve": borrow_asset,
                "Borrow_Day": borrow_day,
                "Borrow_blockNumber": borrow_block,
                "Borrow_Amount": borrow_amount,
                "Last_Repay_Day": [pd.NaT] * len(df_borrow_user),
                "Last_Repay_blockNumber": [np.nan] * len(df_borrow_user),
                "Last_Repay_Amount": [np.nan] * len(df_borrow_user),
                "Time_to_Last_Repay": [pd.NaT] * len(df_borrow_user),
            }
        )
    # Return the resulting DataFrame
    return pd.DataFrame(results)


def first_last_repayment(
    df_borrow_user,
    df_repay_user,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_user="onBehalfOf",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
):
    """
    Combines the results of first and last repayments for a set of borrowing transactions.

    For each borrow entry, this function retrieves:
    - The first repayment that starts covering the borrow (via `first_repayment`)
    - The last repayment that fully covers the borrow (via `last_repayment`)

    It then aligns the two results by index, so that they can be concatenated horizontally.
    Missing values (e.g., unmatched last repayments) are filled with NaN.

    Parameters:
    ----------
    df_borrow_user : pd.DataFrame
        The borrow transactions filtered for a specific user or asset.
    df_repay_user : pd.DataFrame
        The repayment transactions filtered for the same user or asset.
    col_amount : str
        Column name for transaction amount.
    col_cumsum : str
        Column name for cumulative amount column.
    col_user : str
        Column name for the user identifier.
    col_asset : str
        Column name for the asset (e.g., token).
    col_day : str
        Column name for the transaction date.
    col_block : str
        Column name for the block number.

    Returns:
    -------
    df_repayment : DataFrame
        A DataFrame that includes both the first and last repayment information for each borrow.
        Columns from last repayment are appended with NaN if the match does not exist.
    """

    # Compute the first repayment that starts covering each borrow
    first_repay = first_repayment(
        df_borrow_user,
        df_repay_user,
        col_amount,
        col_cumsum,
        col_user,
        col_asset,
        col_day,
        col_block,
    )

    # If missing first repayment: return full row with NaN
    if first_repay.empty:
        return pd.DataFrame(
            {
                "user": df_borrow_user[col_user].values,
                "Reserve": df_borrow_user[col_asset].values,
                "Borrow_Day": df_borrow_user[col_day].values,
                "Borrow_blockNumber": df_borrow_user[col_block].values,
                "Borrow_Amount": df_borrow_user[col_amount].values,
                "First_Repay_Day": [pd.NaT] * len(df_borrow_user),
                "First_Repay_blockNumber": [np.nan] * len(df_borrow_user),
                "First_Repay_Amount": [np.nan] * len(df_borrow_user),
                "Time_to_First_Repay": [pd.NaT] * len(df_borrow_user),
                "Last_Repay_Day": [pd.NaT] * len(df_borrow_user),
                "Last_Repay_blockNumber": [np.nan] * len(df_borrow_user),
                "Last_Repay_Amount": [np.nan] * len(df_borrow_user),
                "Time_to_Last_Repay": [pd.NaT] * len(df_borrow_user),
            }
        )

    # Compute the last repayment that fully covers each borrow
    last_repay = last_repayment(
        df_borrow_user,
        df_repay_user,
        col_amount,
        col_cumsum,
        col_user,
        col_asset,
        col_day,
        col_block,
    )

    # If missing last_repayment
    if last_repay.empty:
        # Create empty columns to align with first_repay (same number of rows)
        last_repay = pd.DataFrame(
            {
                "Last_Repay_Day": [pd.NaT] * len(first_repay),
                "Last_Repay_blockNumber": [np.nan] * len(first_repay),
                "Last_Repay_Amount": [np.nan] * len(first_repay),
                "Time_to_Last_Repay": [pd.NaT] * len(first_repay),
            }
        )

    # Reindex the last repayment DataFrame to match the length and index of first_repay
    last_repay_aligned = last_repay.reindex(first_repay.index)

    # Keep only relevant columns from last repayment info
    cols_to_add = [
        "Last_Repay_Day",
        "Last_Repay_blockNumber",
        "Last_Repay_Amount",
        "Time_to_Last_Repay",
    ]
    last_repay_aligned = last_repay_aligned[cols_to_add]

    # Concatenate first and last repayment information
    df_repayment = pd.concat([first_repay, last_repay_aligned], axis=1)

    return df_repayment


def first_last_repayments_by_user(
    df_borrow,
    df_repay,
    user,
    col_amount="amount",
    col_user_borrow="onBehalfOf",
    col_user_repay="user",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
):
    """
    Computes first and last repayment matches for a given user across all assets the user interacted with.

    For each asset borrowed and repaid by the user, this function:
    - Filters relevant borrow and repay transactions
    - Computes cumulative amounts
    - Matches each borrow with its first and last repayment (via the functions `first_repayment` and `last_repayment`)
    - Concatenates all results into a single DataFrame

    Parameters:
    ----------
    df_borrow_user : pd.DataFrame
        The borrow transactions filtered for a specific user or asset.
    df_repay_user : pd.DataFrame
        The repayment transactions filtered for the same user or asset.
    user : str
        The label of the user.
    col_amount : str
        Column name for transaction amount.
    col_cumsum : str
        Column name for cumulative amount column.
    col_user : str
        Column name for the user identifier.
    col_asset : str
        Column name for the asset (e.g., token).
    col_day : str
        Column name for the transaction date.
    col_block : str
        Column name for the block number.

    Returns:
    -------
    DataFrame with first and last repayment info for each borrow. Missing values are filled with NaN.
    """

    # Filter user-specific borrow and repay transactions
    borrow = df_borrow[df_borrow[col_user_borrow] == user].copy()
    repay = df_repay[df_repay[col_user_repay] == user].copy()

    # Identify shared assets between borrow and repay
    assets = borrow[col_asset].unique()
    all_results = []  # List of DataFrames to concatenate

    for asset in assets:
        # Select relevant borrow and repay events for the asset
        df_borrow_user = borrow[borrow[col_asset] == asset][
            [col_user_borrow, col_day, col_asset, col_amount, col_block]
        ].copy()
        df_borrow_user["Cumsum_amount"] = df_borrow_user[col_amount].cumsum()

        df_repay_user = repay[repay[col_asset] == asset][
            [col_user_repay, col_day, col_asset, col_amount, col_block]
        ].copy()
        df_repay_user["Cumsum_amount"] = df_repay_user[col_amount].cumsum()

        # Compute first and last repayment matches
        df_repay_match = first_last_repayment(
            df_borrow_user,
            df_repay_user,
            col_amount,
            "Cumsum_amount",
            col_user_borrow,
            col_asset,
            col_day,
            col_block,
        )
        # Append to list
        all_results.append(df_repay_match)

    # Concatenate all user-asset level results into a single DataFrame
    df_result = pd.concat(all_results, axis=0, ignore_index=True)

    return df_result


def all_first_last_repayments(
    df_borrow,
    df_repay,
    col_amount="amount",
    col_user_borrow="onBehalfOf",
    col_user_repay="user",
    col_asset="reserve_name",
    col_day="day",
    col_block="blockNumber",
):
    """
    Computes first and last repayment matches for all users across all assets the user interacted with.

    For each asset borrowed and repaid by the user, this function:
    - Filters relevant borrow and repay transactions
    - Computes cumulative amounts
    - Matches each borrow with its first and last repayment (via the functions `first_repayment` and `last_repayment`)
    - Concatenates all results into a single DataFrame

    Parameters:
    ----------
    df_borrow_user : pd.DataFrame
        The borrow transactions filtered for a specific user or asset.
    df_repay_user : pd.DataFrame
        The repayment transactions filtered for the same user or asset.
    col_amount : str
        Column name for transaction amount.
    col_cumsum : str
        Column name for cumulative amount column.
    col_user : str
        Column name for the user identifier.
    col_asset : str
        Column name for the asset (e.g., token).
    col_day : str
        Column name for the transaction date.
    col_block : str
        Column name for the block number.

    Returns:
    -------
    DataFrame with first and last repayment info for each borrow. Missing values are filled with NaN.
    """

    users = df_borrow[col_user_borrow].unique()
    df = DataFrame()
    all_df = []
    for user in users:
        df_user = first_last_repayments_by_user(df_borrow, df_repay, f"{user}")
        all_df.append(df_user)

    return pd.concat(all_df, axis=0, ignore_index=True)
