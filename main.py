# Main ETL

from datetime import datetime
from src.borrows_timespan.timespan_functions import all_first_last_repayments
from src.borrows_timespan.event_funtion_extraction import collect_events_data
from src.borrows_timespan.standardisation import (
    standardisation_borrow,
    standardisation_repay,
    rescaling_borrows,
    rescaling_repay,
)

borrow = "borrow"
repay = "repay"

# Define the time span
# The first data available are on January 27th, 2023
start = datetime(2023, 1, 27)
stop = datetime(2023, 2, 7)

# Collect the data
df_borrow = collect_events_data(event_type=borrow, start=start, stop=stop)
df_repay = collect_events_data(event_type=repay, start=start, stop=stop)

# Rename the assets
df_borrow = standardisation_borrow(df_borrow)
df_repay = standardisation_repay(df_repay)

# Rescale the amounts
df_borrow = rescaling_borrows(df_borrow)
df_repay = rescaling_repay(df_repay)

# Create the dataframe
df = all_first_last_repayments(df_borrow, df_repay)
print(df)
