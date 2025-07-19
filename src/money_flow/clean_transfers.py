from web3 import Web3
from hexbytes import HexBytes


def classify_addresses(top_borrowers, alchemy_api_key):
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

    # Create the 'address' column based on direction
    top_borrowers["address"] = top_borrowers.apply(
        lambda row: row["to"] if row["direction"] == "sent" else row["from"], axis=1
    )

    # Build mapping of unique addresses to their type
    address_types_user = {}
    unique_addresses_user = top_borrowers["user"].astype(str).unique()

    for addr in unique_addresses_user:
        try:
            checksum_addr = w3.to_checksum_address(addr)
            code = w3.eth.get_code(checksum_addr)
            if code == HexBytes("0x"):
                address_types_user[addr] = "Address"
            else:
                address_types_user[addr] = "Contract"
        except Exception as e:
            print(f"Error with address {addr}: {e}")
            address_types_user[addr] = "Unknown"

    # Map the classification back to the DataFrame
    top_borrowers["user_type"] = top_borrowers["user"].map(address_types_user)
    return top_borrowers
