# map the token
token_mapping_borrow = {
    "0xD533a949740bb3306d119CC777fa900bA034cd52": "CRV",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
    "0xae78736Cd615f374D3085123A210448E74Fc6393": "rETH",
    "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f": "ankrETH",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI",
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",
    "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2": "MKR",
    "0x5f98805A4E8be255a32880FDeC7F6728C6568bA0": "LUSD",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC",
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": "UNI",
    "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0": "wstETH",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": "LINK",
    "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E": "cstETH",
    "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704": "cbETH",
    "0x853d955aCEf822Db058eb8505911ED77F175b99e": "FRAX",
    "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32": "LDO",
    "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72": "ENS",
    "0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0": "FXS",
    "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F": "SNX",
    "0xD33526068D116cE69F19A9ee46F0bd304F21A51f": "RPL",
    "0x111111111117dC0aa78b770fA6A738034120C302": "1INCH",
    "0xdeFA4e8a7bcBA345F687a2f1456F5Edd9CE97202": "FXS",
}


token_mapping_repay = {
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",
    "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",
    "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704": "cbETH",
    "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0": "wstETH",
    "0xba100000625a3754423978a60c9317c58a424e3D": "BAL",
    "0xD533a949740bb3306d119CC777fa900bA034cd52": "CRV",
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2": "WETH",
    "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI",
    "0xD33526068D116cE69F19A9ee46F0bd304F21A51f": "RPL",
    "0xdeFA4e8a7bcBA345F687a2f1456F5Edd9CE97202": "FXS",
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599": "WBTC",
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": "UNI",
    "0xae78736Cd615f374D3085123A210448E74Fc6393": "rETH",
    "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f": "ankrETH",
    "0xAf5191B0De278C7286d6C7CC6ab6BB8A73bA2Cd6": "LBR",
    "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E": "cstETH",
    "0x5f98805A4E8be255a32880FDeC7F6728C6568bA0": "LUSD",
    "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F": "SNX",
    "0x111111111117dC0aa78b770fA6A738034120C302": "1INCH",
    "0x853d955aCEf822Db058eb8505911ED77F175b99e": "FRAX",
    "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32": "LDO",
    "0x514910771AF9Ca656af840dff83E8264EcF986CA": "LINK",
    "0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0": "FXS",
    "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2": "MKR",
}


token_mapping_decimals = {
    "USDC": 6,
    "USDT": 6,
    "cbETH": 18,
    "wstETH": 18,
    "BAL": 18,
    "CRV": 18,
    "WETH": 18,
    "DAI": 18,
    "RPL": 18,
    "FXS": 18,
    "WBTC": 8,
    "UNI": 18,
    "rETH": 18,
    "ankrETH": 18,
    "LBR": 18,
    "cstETH": 18,
    "LUSD": 18,
    "SNX": 18,
    "1INCH": 18,
    "FRAX": 18,
    "LDO": 18,
    "LINK": 18,
    "MKR": 18,
    "ENS": 18,
}


def standardisation_borrow(df_borrow):
    """
    Function aiming at renaming the name of the assets on smart contracts by their name.

    Parameters:
    -----------
    df_borrow : pd.DataFrame
        Borrowing transactions.

    Returns:
    --------
    pd.DataFrame
        Dataframe of borrows in which the assets are renammed.
    """
    # Add a new column with the name of the crypto
    df_borrow["name"] = df_borrow["reserve"].map(token_mapping_borrow)
    # relocate the last column created after the column "reserve"
    df_borrow.insert(loc=2, column="reserve_name", value=df_borrow["name"])
    # delete the last column
    df_borrow.drop(columns="name", inplace=True)
    return df_borrow


def standardisation_repay(df_repay):
    """
    Function aiming at renaming the name of the assets on smart contracts by their name.

    Parameters:
    -----------
    df_repay : pd.DataFrame
        Repayment transactions.

    Returns:
    --------
    pd.DataFrame
        Dataframe of repayments in which the assets are renammed.
    """
    # Add a new column with the name of the crypto
    df_repay["name"] = df_repay["reserve"].map(token_mapping_repay)
    # relocate the last column created after the column "reserve"
    df_repay.insert(loc=2, column="reserve_name", value=df_repay["name"])
    # delete the last column
    df_repay.drop(columns="name", inplace=True)
    return df_repay


def rescaling_borrows(df_borrow):
    """
    Function that rescale the amounts borrowed and repaid.

    Parameters:
    -----------
    df_borrow : pd.DataFrame
        Borrowing transactions.
    df_repay : pd.DataFrame
        Repayment transactions.

    Returns:
    --------
    pd.DataFrame
        Dataframe of borrows and repayments in which the values of the transactions are correctly rescaled.

    """
    # Maps the decimals and the asset of both datasets
    df_borrow["decimals"] = df_borrow["reserve_name"].map(token_mapping_decimals)

    # Rescale the values of transactions
    df_borrow["amount"] = (df_borrow["amount"] / (10 ** df_borrow["decimals"])).round(6)
    return df_borrow


def rescaling_repay(df_repay):
    """
    Function that rescale the amounts borrowed and repaid.

    Parameters:
    -----------
    df_repay : pd.DataFrame
        Borrowing transactions.

    Returns:
    --------
    pd.DataFrame
        Dataframe of repayments in which the values of the transactions are correctly rescaled.

    """
    # Maps the decimals and the asset of both datasets
    df_repay["decimals"] = df_repay["reserve_name"].map(token_mapping_decimals)

    # Rescale the values of transactions
    df_repay["amount"] = (df_repay["amount"] / (10 ** df_repay["decimals"])).round(6)
    return df_repay
