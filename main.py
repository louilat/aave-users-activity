# Main ETL
import pandas as pd
import boto3
import json
from datetime import datetime
from src.borrows_timespan.timespan_functions import (
    all_first_last_repayments,
    collect_borrow_repay,
)
from src.borrows_timespan.standardisation import (
    add_timestamp,
    classify_addresses,
    fetch_erc20_metadata,
)
from src.borrows_timespan.data_extraction import (
    extract_user_transactions,
)

# Inputs
YOUR_ACCESS_KEY = "INPUT_YOUR_ACCESS_KEY"
YOUR_SECRET_KEY = "INPUT_YOUR_SECRET_KEY"
YOUR_TOKEN = "INPUT_YOUR_TOKEN"
KEY = "INPUT_YOUR_ALCHEMY_API_KEY"


# Define the time span
# The first data available are on January 27th, 2023
start = datetime(2023, 1, 27)
stop = datetime(2023, 2, 7)

# Collect the data
df_borrow, df_repay = collect_borrow_repay(start=start, stop=stop)

# Create the dataframe
df = all_first_last_repayments(df_borrow, df_repay)

client_s3 = boto3.client(
    "s3",
    endpoint_url="https://" + "minio.lab.sspcloud.fr",
    aws_access_key_id=f"{YOUR_ACCESS_KEY}",
    aws_secret_access_key=f"{YOUR_SECRET_KEY}",
    aws_session_token=f"{YOUR_TOKEN}",
    verify=False,
)

data = client_s3.get_object(
    Bucket="arnaudbrrt",
    Key=f"/diffusion/aave_user_activity/blocksTimestamps.json",
)["Body"].read()
blocks_timestamps = json.loads(data)

blocksTimestamps = pd.DataFrame(blocks_timestamps)

df = add_timestamp(
    df=df,
    blocksTimestamps=blocksTimestamps,
    col_blockNumber_borrow="Borrow_blockNumber",
    col_day_borrow="Borrow_Day",
    col_blockNumber_first="First_Repay_blockNumber",
    col_day_first="First_Repay_Day",
    col_blockNumber_last="Last_Repay_blockNumber",
    col_day_last="Last_Repay_Day",
)

df = extract_user_transactions(df=df, alchemy_api_key=KEY)

df = classify_addresses(df=df, alchemy_api_key=KEY)

df = fetch_erc20_metadata(df=df, alchemy_api_key=KEY)

df.to_csv("data/df_tx.csv", index=False)
