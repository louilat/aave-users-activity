# Main ETL

from datetime import datetime
from src.borrows_timespan.timespan_functions import (
    all_first_last_repayments,
    collect_borrow_repay,
)
from src.borrows_timespan.standardisation import (
    add_timestamp,
)
from src.borrows_timespan.data_extraction import (
    get_user_transactions_sent,
    get_user_transactions_received,
)

# Define the time span
# The first data available are on January 27th, 2023
start = datetime(2023, 1, 27)
stop = datetime(2023, 2, 7)

# Collect the data
df_borrow, df_repay = collect_borrow_repay(start=start, stop=stop)

# Create the dataframe
df = all_first_last_repayments(df_borrow, df_repay)

df = add_timestamp(
    df,
    blocksTimestamps="data/blocksTimestamps.json",
    col_blockNumber_df_borrow="Borrow_blockNumber",
    col_day_borrow="Borrow_Day",
    col_blockNumber_df_first="First_Repay_blockNumber",
    col_day_first="First_Repay_Day",
    col_blockNumber_df_last="Last_Repay_blockNumber",
    col_day_last="Last_Repay_Day",
)

df.to_csv("data/borrows_timespan_outputs.csv", index=False)

key = "YOUR_ALCHEMY_API_KEY"

ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{key}"

tx_sent = get_user_transactions_sent(
    ALCHEMY_URL=ALCHEMY_URL,
    address=df["user"],
    from_block=df["Borrow_blockNumber"],
    to_block=df["First_Repay_blockNumber"],
)
tx_received = get_user_transactions_received(
    ALCHEMY_URL=ALCHEMY_URL,
    address=df["user"],
    from_block=df["Borrow_blockNumber"],
    to_block=df["Last_Repay_blockNumber"],
)
