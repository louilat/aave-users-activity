import pandas as pd
import numpy as np


def get_tx_flow(
    df_transactions,
    user="user",
    blockNumber="blockNumber",
    hash="tx_hash",
    asset="asset",
    value="value",
):
    """
    This function processes a transaction DataFrame to identify, for each user,
    pairs of incoming and outgoing asset flows where the cumulative outgoing amount
    matches or exceeds the incoming amount over time. It also enriches the original
    dataset by attaching an index_transfer identifier to each transaction.

    Parameters:
    - df_transactions: pandas DataFrame containing transaction data.
    - user: column name identifying users.
    - blockNumber: column name for the block number.
    - hash: column name for the transaction hash.
    - asset: column name for the asset type.
    - value: column name for the transaction value (positive for in, negative for out).

    Returns:
    - A pandas DataFrame matching the input but enriched with 'index_transfer'.
    """

    all_user_flows = []  # List to collect flows for all users

    # Loop over each unique user
    for borrower in df_transactions[user].unique():
        # Filter transactions for the current user
        user_transactions = df_transactions[df_transactions[user] == borrower]

        # Aggregate transaction amounts per blockNumber, hash, and asset
        aggregated_flows = (
            user_transactions.groupby([blockNumber, hash, asset])
            .agg({value: "sum"})
            .reset_index()
        )

        # Sort transactions by block number to maintain temporal order
        aggregated_flows = aggregated_flows.sort_values(blockNumber)

        # Assign the transfer direction based on the sign of the amount
        aggregated_flows["direction"] = np.where(
            aggregated_flows[value] > 0, "IN", "OUT"
        )

        # Separate incoming and outgoing transfers
        incoming_transfers = aggregated_flows[aggregated_flows[value] > 0]
        outgoing_transfers = aggregated_flows[aggregated_flows[value] < 0]

        # Merge incoming and outgoing transfers on asset to pair them
        matched_flows = incoming_transfers.merge(
            outgoing_transfers, on=asset, suffixes=("_in", "_out")
        )

        # Keep only pairs where the outgoing transfer occurs after the incoming transfer
        matched_flows = matched_flows[
            matched_flows[blockNumber + "_in"] <= matched_flows[blockNumber + "_out"]
        ]

        # Make outgoing amounts positive for comparison
        matched_flows[value + "_out"] = matched_flows[value + "_out"].abs()

        # Compute cumulative outgoing amount per incoming transfer
        matched_flows["cumulative_out"] = matched_flows.groupby(
            [blockNumber + "_in", hash + "_in", asset]
        )[value + "_out"].cumsum()

        # Flag rows where cumulative outgoing exceeds incoming
        matched_flows["exceed"] = (
            matched_flows["cumulative_out"] >= matched_flows[value + "_in"]
        )

        # Count the occurrences of exceedance per incoming transaction
        matched_flows["count_exceed"] = matched_flows.groupby(
            [blockNumber + "_in", hash + "_in", asset]
        )["exceed"].cumsum()

        # Keep only the first occurrence of exceedance
        matched_flows = matched_flows[matched_flows["count_exceed"] <= 1]

        # Add the user identifier
        matched_flows[user] = borrower

        # Append to the list
        all_user_flows.append(matched_flows)

    # Concatenate all users' flows into a single DataFrame
    df_all_flows = pd.concat(all_user_flows, ignore_index=True)

    # Reorder columns to have the user column first
    df_all_flows = df_all_flows[
        [df_all_flows.columns[-1]] + list(df_all_flows.columns[:-1])
    ]

    # Create a unique index_transfer identifier
    df_all_flows["index_transfer"] = df_all_flows["count_exceed"].cumsum()

    # Build DataFrame for incoming transfers with standardized column names
    incoming_flows_renamed = df_all_flows.rename(
        columns={
            "blockNumber_in": "blockNumber",
            "tx_hash_in": "tx_hash",
            "value_in": "value",
        }
    )[[user, "blockNumber", "tx_hash", "asset", "value", "index_transfer"]]

    # Build DataFrame for outgoing transfers with standardized column names
    outgoing_flows_renamed = df_all_flows.rename(
        columns={
            "blockNumber_out": "blockNumber",
            "tx_hash_out": "tx_hash",
            "value_out": "value",
        }
    )[[user, "blockNumber", "tx_hash", "asset", "value", "index_transfer"]]

    # Concatenate incoming and outgoing transfers together
    df_all_transfers = pd.concat(
        [incoming_flows_renamed, outgoing_flows_renamed], ignore_index=True
    )

    # Remove duplicate rows to ensure one index_transfer per transaction
    df_transfers_unique = df_all_transfers.drop_duplicates(
        subset=[user, "tx_hash", "asset", "blockNumber"], keep="first"
    )

    # Merge the unique index_transfer back into the original transactions
    df_transactions_enriched = df_transactions.merge(
        df_transfers_unique,
        how="left",
        on=[user, "tx_hash", "asset", "blockNumber", "value"],
    )

    # Return the enriched DataFrame
    return df_transactions_enriched


def group_transfers_by_contracts(df_flow_of_user, address="address"):
    """
    This function assigns a unique integer ID to each distinct contract or address in the input DataFrame.

    Args:
        df_flow_of_user (pd.DataFrame): The DataFrame containing transfer data.
        address (str): The column name that contains addresses or contract identifiers.

    Returns:
        pd.DataFrame: A copy of the input DataFrame with an additional column 'contract_number'
                      mapping each unique address to an integer label.
    """

    # Extract unique addresses from the specified column
    unique_addresses = df_flow_of_user[address].unique()

    # Build a mapping dictionary associating each address to a unique integer
    address_mapping = {addr: idx for idx, addr in enumerate(unique_addresses)}

    # Map each address in the DataFrame to its integer ID
    df_flow_of_user["contract_number"] = df_flow_of_user[address].map(address_mapping)

    # Return the DataFrame with the new column
    return df_flow_of_user


def all_swaps(df_flow_of_user, tx_hash="tx_hash", asset="asset", value="value"):
    """
    This function identifies swaps within transactions and annotates the DataFrame with the received token(s).

    For each transaction hash, it checks if there is at least one positive and one negative transfer.
    If so, it assigns the received token for each negative transfer, following these rules:
    - If the negative asset starts with 'a', 'variableDebt', or 'variableDebtEth', the received token must match the suffix after the prefix.
    - Otherwise, the first positive token (in sorted order) is assigned.

    Args:
        df_flow_of_user (pd.DataFrame): The DataFrame containing transaction flow data.
        tx_hash (str): Column name indicating the transaction identifier.
        asset (str): Column name indicating the asset/token.
        value (str): Column name indicating the numeric value of the transfer.

    Returns:
        pd.DataFrame: The input DataFrame with a new column 'Token_Received_By_Swap'
                      indicating the received token for each negative transfer.
    """

    # Initialize the column
    df_flow_of_user["Token_Received_By_Swap"] = np.nan

    # List of known prefixes
    prefixes = ["a", "variableDebt", "variableDebtEth"]

    # Loop over each transaction
    for tx, group in df_flow_of_user.groupby(tx_hash):
        # Skip transactions with only one transfer
        if len(group) <= 1:
            continue

        # Create mask for transfers where value != 0
        mask_valid_value = group[value] != 0.0

        # Masks for positive and negative transfers
        mask_positive = mask_valid_value & (group[value] > 0)
        mask_negative = mask_valid_value & (group[value] < 0)

        # Check if there is at least one positive and one negative transfer
        has_positive = any(mask_positive)
        has_negative = any(mask_negative)

        if has_positive and has_negative:
            # Collect unique positive assets
            positive_assets = sorted(set(group.loc[mask_positive, asset]))

            # Get indices of negative rows
            mask_negative_global = (df_flow_of_user[tx_hash] == tx) & (
                df_flow_of_user[value] < 0
            )
            negative_indices = df_flow_of_user.loc[mask_negative_global].index

            # Loop over each negative transfer
            for idx in negative_indices:
                neg_asset = df_flow_of_user.at[idx, asset]

                # Check if the asset has a prefix
                matching_prefix = None
                for prefix in prefixes:
                    if neg_asset.startswith(prefix):
                        matching_prefix = prefix
                        break

                if matching_prefix:
                    # Extract suffix (the expected received token)
                    suffix = neg_asset[len(matching_prefix) :]
                    # Check if this suffix was actually received
                    if suffix in positive_assets:
                        df_flow_of_user.at[idx, "Token_Received_By_Swap"] = suffix
                    else:
                        # Not matching the expected token
                        df_flow_of_user.at[idx, "Token_Received_By_Swap"] = np.nan
                else:
                    # For normal assets, assign the first positive token
                    if positive_assets:
                        df_flow_of_user.at[idx, "Token_Received_By_Swap"] = (
                            positive_assets[0]
                        )
                    else:
                        df_flow_of_user.at[idx, "Token_Received_By_Swap"] = np.nan

    return df_flow_of_user

''' CODE TO GET THE FLOW 

from collections import deque

user_address = unique_users[53]

df_user = df_flow[df_flow["user"] == user_address]

first_block_number = df_user.loc[df_user["user"] == user_address, "blockNumber"].min()

df_user = get_tx_flow(df_user)
df_user = group_transfers_by_contracts(df_user)
df_user = all_swaps(df_user)


mask = (
    (df_user["blockNumber"] == first_block_number)
    & (df_user["asset"].str.startswith("variableDebt"))
    & (df_user["direction"] == "received")
)

initial_rows = df_user[mask]

G = nx.DiGraph()

queue = deque()
for _, row in initial_rows.iterrows():
    queue.append(row)

processed_rows = set()

while queue:
    current_row = queue.popleft()

    current_asset = current_row["asset"]
    current_index = current_row["index_transfer"]
    current_block = current_row["blockNumber"]
    current_contract = current_row["contract_number"]

    # Create a unique node name using asset + index_transfer
    current_node = f"{current_asset}_idx{current_index}"

    # Avoid reprocessing exactly the same node
    if (current_asset, current_index, current_block) in processed_rows:
        continue
    processed_rows.add((current_asset, current_index, current_block))

    ### Outgoing transfers from this index_transfer
    mask_outgoing = (df_user["index_transfer"] == current_index) & (
        df_user["value"] < 0
    )
    outgoing_rows = df_user.loc[mask_outgoing]

    for _, out_row in outgoing_rows.iterrows():
        out_asset = out_row["asset"]
        out_index = out_row["index_transfer"]
        out_node = f"{out_asset}_idx{out_index}"

        # Add edge
        G.add_edge(current_node, out_node, label="transfer")

        # Add to queue
        queue.append(out_row)

    ### Swaps
    if pd.notna(current_row["Token_Received_By_Swap"]):
        swap_asset = current_row["Token_Received_By_Swap"]
        # Find all rows corresponding to the swap asset
        swap_rows = df_user[df_user["asset"] == swap_asset]
        for _, swap_row in swap_rows.iterrows():
            swap_index = swap_row["index_transfer"]
            swap_node = f"{swap_asset}_idx{swap_index}"

            # Add edge
            G.add_edge(current_node, swap_node, label="swap")

            # Add to queue
            queue.append(swap_row)

    ### Next transfer by contract_number
    mask_next = (df_user["contract_number"] == current_contract) & (
        df_user["blockNumber"] >= current_block
    )
    next_rows = df_user.loc[mask_next].sort_values("blockNumber").head(1)
    for _, next_row in next_rows.iterrows():
        next_asset = next_row["asset"]
        next_index = next_row["index_transfer"]
        next_node = f"{next_asset}_idx{next_index}"

        # Add edge
        G.add_edge(current_node, next_node, label="next_transfer")

        # Add to queue
        queue.append(next_row)
'''