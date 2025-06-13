# Borrow timespan functions

import pandas as pd
import numpy as np


def repayment(
    df_borrow_user,
    df_repay_user,
    first_repay=True,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_user="onBehalfOf",
    col_asset="name",
    col_day="day",
    col_block="blockNumber",
    col_USD="underlyingEventPriceUSD",
):
    """
    Match each borrowing transaction with the first repayment transaction that
    cumulatively repays it, for the same user and reserve (asset).

    This generalized version accepts flexible column names as arguments so it can be reused
    across different datasets with similar structure but different field names.

    Parameters:
        df_borrow_user (DataFrame): Filtered borrowing transactions for a specific user.
        df_repay_user (DataFrame): Filtered repayment transactions for the same user.
        Threshold (bool): True if we want the first repayment. By default, Threshold = True.
        col_amount (str): Column name for the transaction amount.
        col_cumsum (str): Column name for the cumulative sum of repayments.
        col_user (str): Column name for the user address.
        col_asset (str): Column name for the token/reserve name.
        col_day (str): Column name for the transaction day or timestamp.
        col_block (str): Column name for the block number.

    Returns:
        pd.DataFrame: A table where each row maps a borrow to its corresponding covering repayment.
    """
    # Define prefix for repayment columns based on mode
    prefix = "First" if first_repay else "Last"

    # If there are no repayments, return a DataFrame with NaNs for repayment fields
    if df_repay_user.empty:
        return pd.DataFrame(
            {
                "user": df_borrow_user[col_user].values,
                "Reserve": df_borrow_user[col_asset].values,
                "Borrow_Day": df_borrow_user[col_day].values,
                "Borrow_blockNumber": df_borrow_user[col_block].values,
                "Borrow_Amount": df_borrow_user[col_amount].values,
                "Borrow_USD_Price": df_borrow_user[col_USD].values,
                f"{prefix}_Repay_Day": [pd.NaT] * len(df_borrow_user),
                f"{prefix}_Repay_blockNumber": [np.nan] * len(df_borrow_user),
                f"{prefix}_Repay_Amount": [np.nan] * len(df_borrow_user),
                f"{prefix}_Repay_Amount_USD": [np.nan] * len(df_borrow_user),
                f"Time_to_{prefix}_Repay": [pd.NaT] * len(df_borrow_user),
            }
        )

    # List to store results for each borrow transaction
    results = []

    # Extract repayment-related arrays for efficient access
    repay_cumsum = df_repay_user[col_cumsum].values
    repay_day = df_repay_user[col_day].values
    repay_block = df_repay_user[col_block].values
    repay_amount = df_repay_user[col_amount].values
    repay_amount_USD = df_repay_user[col_USD].values

    # Extract borrowing-related arrays for efficient access
    borrow_cumsum = df_borrow_user[col_cumsum].values
    borrow_amount = df_borrow_user[col_amount].values
    borrow_amount_USD = df_borrow_user[col_USD].values
    borrow_day = df_borrow_user[col_day].values
    borrow_block = df_borrow_user[col_block].values
    borrow_user = df_borrow_user[col_user].values
    borrow_asset = df_borrow_user[col_asset].values

    # Loop over each borrowing transaction
    for index_borrow in range(len(df_borrow_user)):
        # Define the repayment threshold depending on the mode
        # For Threshold=True: find the first repayment
        # For Threshold=False: find the last repayment
        threshold = (
            0
            if index_borrow == 0 and first_repay
            else borrow_cumsum[index_borrow - 1]
            if first_repay
            else borrow_cumsum[index_borrow]
        )

        # Find the first repayment that meets both block and threshold conditions
        for index_repay in range(len(df_repay_user)):
            if (
                repay_block[index_repay] >= borrow_block[index_borrow]
                and repay_cumsum[index_repay] > threshold
            ):
                # If match is found, store the match and stop checking further repayments
                results.append(
                    {
                        "user": borrow_user[index_borrow],
                        "Reserve": borrow_asset[index_borrow],
                        "Borrow_Day": borrow_day[index_borrow],
                        "Borrow_blockNumber": borrow_block[index_borrow],
                        "Borrow_Amount": borrow_amount[index_borrow],
                        "Borrow_USD_Price": borrow_amount_USD[index_borrow],
                        f"{prefix}_Repay_Day": repay_day[index_repay],
                        f"{prefix}_Repay_blockNumber": repay_block[index_repay],
                        f"{prefix}_Repay_Amount": repay_amount[index_repay],
                        f"{prefix}_Repay_Amount_USD": repay_amount_USD[index_repay],
                        f"Time_to_{prefix}_Repay": repay_day[index_repay]
                        - borrow_day[index_borrow],
                    }
                )
                break  # stop after first match

        else:
            # If no repayment matched, fill the row with NaNs
            results.append(
                {
                    "user": borrow_user[index_borrow],
                    "Reserve": borrow_asset[index_borrow],
                    "Borrow_Day": borrow_day[index_borrow],
                    "Borrow_blockNumber": borrow_block[index_borrow],
                    "Borrow_Amount": borrow_amount[index_borrow],
                    "Borrow_USD_Price": borrow_amount_USD[index_borrow],
                    f"{prefix}_Repay_Day": pd.NaT,
                    f"{prefix}_Repay_blockNumber": np.nan,
                    f"{prefix}_Repay_Amount": np.nan,
                    f"{prefix}_Repay_Amount_USD": np.nan,
                    f"Time_to_{prefix}_Repay": pd.NaT,
                }
            )

    # Convert list of results to a DataFrame and return it
    return pd.DataFrame(results)


def first_last_repayment(
    df_borrow_user,
    df_repay_user,
    col_amount="amount",
    col_cumsum="Cumsum_amount",
    col_user="onBehalfOf",
    col_asset="name",
    col_day="day",
    col_block="blockNumber",
    col_USD="underlyingEventPriceUSD",
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
    col_USD : str
        Column name for the underlying USD Price of the Token

    Returns:
    -------
    df_repayment : DataFrame
        A DataFrame that includes both the first and last repayment information for each borrow.
        Columns from last repayment are appended with NaN if the match does not exist.
    """

    # Compute the first repayment that starts covering each borrow
    first_repay = repayment(
        df_borrow_user,
        df_repay_user,
        first_repay=True,
        col_amount=col_amount,
        col_cumsum=col_cumsum,
        col_user=col_user,
        col_asset=col_asset,
        col_day=col_day,
        col_block=col_block,
        col_USD=col_USD,
    )

    # Compute the last repayment that fully covers each borrow
    last_repay = repayment(
        df_borrow_user,
        df_repay_user,
        first_repay=False,
        col_amount=col_amount,
        col_cumsum=col_cumsum,
        col_user=col_user,
        col_asset=col_asset,
        col_day=col_day,
        col_block=col_block,
        col_USD=col_USD,
    )

    cols_to_add = [
        "Last_Repay_Day",
        "Last_Repay_blockNumber",
        "Last_Repay_Amount",
        "Last_Repay_Amount_USD",
        "Time_to_Last_Repay",
    ]

    # Merge first and last repayment information on the borrow keys
    merge_keys = [
        "user",
        "Reserve",
        "Borrow_Day",
        "Borrow_blockNumber",
        "Borrow_Amount",
        "Borrow_USD_Price",
    ]

    df_repayment = first_repay.merge(
        last_repay[merge_keys + cols_to_add], on=merge_keys, how="inner"
    )
    print(df_repayment)
    assert len(df_repayment) == len(df_borrow_user)

    return df_repayment


def first_last_repayments_by_user(
    df_borrow_user,
    df_repay_user,
    col_amount="amount",
    col_user_borrow="onBehalfOf",
    col_user_repay="user",
    col_asset="name",
    col_day="day",
    col_block="blockNumber",
    col_USD="underlyingEventPriceUSD",
):
    """
    Computes first and last repayment matches for a given user across all assets the user borrowed with.

    For each asset borrowed and repaid by the user, this function:
    - Filters relevant borrow and repay transactions
    - Computes cumulative amounts
    - Matches each borrow with its first and last repayment (via the functions `first_repayment` and `last_repayment`)
    - Concatenates all results into a single DataFrame

    Parameters:
    ----------
    df_borrow_user : pd.DataFrame
        The borrow transactions of a user.
    df_repay_user : pd.DataFrame
        The repayment transactions of a user.
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
    col_USD : str
        Column name for the underlying USD Price of the Token

    Returns:
    -------
    DataFrame with first and last repayment info for each borrow. Missing values are filled with NaN.
    """

    # Identify shared assets between borrow and repay
    assets = df_borrow_user[col_asset].unique()
    all_results = []  # List of DataFrames to concatenate

    for asset in assets:
        # Select relevant borrow and repay events for the asset
        df_borrow_user = df_borrow_user[df_borrow_user[col_asset] == asset][
            [col_user_borrow, col_day, col_asset, col_amount, col_USD, col_block]
        ].copy()
        df_borrow_user["Cumsum_amount"] = df_borrow_user[col_amount].cumsum()

        df_repay_user = df_repay_user[df_repay_user[col_asset] == asset][
            [col_user_repay, col_day, col_asset, col_amount, col_USD, col_block]
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
            col_USD,
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
    col_asset="name",
    col_day="day",
    col_block="blockNumber",
    col_USD="underlyingEventPriceUSD",
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
    col_USD : str
        Column name for the underlying USD Price of the Token

    Returns:
    -------
    DataFrame with first and last repayment info for each borrow. Missing values are filled with NaN.
    """
    users = df_borrow[col_user_borrow].unique()
    all_df = []
    for user in users:
        # Filter user-specific borrow and repay transactions
        borrow = df_borrow[df_borrow[col_user_borrow] == user].copy()
        repay = df_repay[df_repay[col_user_repay] == user].copy()

        df_user = first_last_repayments_by_user(
            borrow,
            repay,
            col_amount=col_amount,
            col_user_borrow=col_user_borrow,
            col_user_repay=col_user_repay,
            col_asset=col_asset,
            col_day=col_day,
            col_block=col_block,
            col_USD=col_USD,
        )
        all_df.append(df_user)

    return pd.concat(all_df, axis=0, ignore_index=True)
