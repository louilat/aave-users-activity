# map the token
import pandas as pd


def rescaling_borrow(df_borrow, reserves):
    """
    Function that merge the dataframe of borrows and of reserves to get the underlying price in USD and the decimals
    necessary to rescale the amounts.

    Parameters:
    -----------
    df_borrow : pd.DataFrame
        Borrowing transactions.
    reserves : pd.DataFrame
        Characteristics of assets every day.

    Returns:
    --------
    pd.DataFrame
        Dataframe of borrows in which the values of the transactions are correctly rescaled and the column reordered.

    """
    # Merge the two dataframe
    df_borrow = pd.merge(
        df_borrow,
        reserves[
            ["day", "name", "decimals", "underlyingAsset", "underlyingTokenPriceUSD"]
        ],
        how="left",
        left_on=["reserve", "day"],
        right_on=["underlyingAsset", "day"],
    )

    # Rescale the values of transactions
    df_borrow["amount"] = (
        (df_borrow["amount"] / (10 ** df_borrow["decimals"])).astype(float).round(6)
    )

    # Calculate the USD price of the borrow
    df_borrow["underlyingEventPriceUSD"] = (
        df_borrow["underlyingTokenPriceUSD"] * df_borrow["amount"]
    )

    # Reorder columns after ther merge
    new_order_borrow = [
        "blockNumber",
        "reserve",
        "name",
        "decimals",
        "onBehalfOf",
        "user",
        "amount",
        "underlyingEventPriceUSD",
        "underlyingTokenPriceUSD",
        "day",
    ]
    df_borrow = df_borrow[new_order_borrow]
    df_borrow["amount"].astype("float64")
    df_borrow.groupby(
        [
            "blockNumber",
            "reserve",
            "name",
            "decimals",
            "onBehalfOf",
            "user",
            "underlyingEventPriceUSD",
            "underlyingTokenPriceUSD",
            "day",
        ],
        as_index=False,
    ).sum({"amount": "sum"})
    return df_borrow


def rescaling_repay(df_repay, reserves):
    """
    Function that merge the dataframe of borrows and of reserves to get the underlying price in USD and the decimals
    necessary to rescale the amounts.

    Parameters:
    -----------
    df_repay : pd.DataFrame
        Repayment transactions.
    reserves : pd.DataFrame
        Characteristics of assets every day.

    Returns:
    --------
    pd.DataFrame
        Dataframe of repayments in which the values of the transactions are correctly rescaled and the column reordered.

    """
    # Merge the two dataframe
    df_repay = pd.merge(
        df_repay,
        reserves[
            ["day", "name", "decimals", "underlyingAsset", "underlyingTokenPriceUSD"]
        ],
        how="left",
        left_on=["reserve", "day"],
        right_on=["underlyingAsset", "day"],
    )

    # Rescale the values of transactions
    df_repay["amount"] = (
        (df_repay["amount"] / (10 ** df_repay["decimals"])).astype(float).round(6)
    )

    # Calculate the USD price of the repay
    df_repay["underlyingEventPriceUSD"] = (
        df_repay["underlyingTokenPriceUSD"] * df_repay["amount"]
    )

    # Reorder columns
    new_order_repay = [
        "blockNumber",
        "reserve",
        "name",
        "decimals",
        "user",
        "repayer",
        "amount",
        "underlyingEventPriceUSD",
        "underlyingTokenPriceUSD",
        "useATokens",
        "day",
    ]
    df_repay = df_repay[new_order_repay]
    df_repay["amount"].astype("float64")
    df_repay.groupby(
        [
            "blockNumber",
            "reserve",
            "name",
            "decimals",
            "user",
            "repayer",
            "underlyingEventPriceUSD",
            "underlyingTokenPriceUSD",
            "day",
        ],
        as_index=False,
        ).sum({"amount": "sum"})
    return df_repay
