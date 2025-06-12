# Main ETL

from datetime import datetime
from src.borrows_timespan.timespan_functions import all_first_last_repayments
from src.borrows_timespan.data_extraction import (
    collect_events_data,
    collect_reserves_data,
)
from src.borrows_timespan.standardisation import rescaling_borrow, rescaling_repay

borrow = "borrow"
repay = "repay"

# Define the time span
# The first data available are on January 27th, 2023
start = datetime(2023, 1, 27)
stop = datetime(2023, 2, 7)

# Collect the data
df_borrow = collect_events_data(event_type=borrow, start=start, stop=stop)
df_repay = collect_events_data(event_type=repay, start=start, stop=stop)
reserves = collect_reserves_data(start=start, stop=stop)

# Rescale the df
df_borrow = rescaling_borrow(df_borrow, reserves)
df_repay = rescaling_repay(df_repay, reserves)

# Create the dataframe
df = all_first_last_repayments(df_borrow, df_repay)
