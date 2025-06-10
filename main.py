# Main ETL
import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "src/borrows_timespan"))

import borrows_timespan as bt
import event_funtion_extraction as event
import standardisation as standard

borrow = "borrow"
repay = "repay"

# Define the time span
# The first data available are on January 27th, 2023
start = datetime(2023, 1, 27)
stop = datetime(2023, 2, 7)

# Collect the data
df_borrow = event.collect_events_data(event_type=borrow, start=start, stop=stop)
df_repay = event.collect_events_data(event_type=repay, start=start, stop=stop)

# Rename the assets
df_borrow = standard.standardisation_borrow(df_borrow)
df_repay = standard.standardisation_repay(df_repay)

# Rescale the amounts
df_borrow = standard.rescaling_borrows(df_borrow)
df_repay = standard.rescaling_repay(df_repay)

# Create the dataframe
df = bt.all_first_last_repayments(df_borrow, df_repay)
print(df)
