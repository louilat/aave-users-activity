import pandas as pd
from pandas import DataFrame
import requests
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")


def collect_events_data(event_type: str, start: datetime, stop: datetime) -> DataFrame:
    """
    Collect the users events data from the api endpoint for a given time interval.
    Args:
        event_type (str): One of the following "borrow", "repay", "supply", "withdraw"
        start (datetime): The date at which the data collection starts.
        stop (datetime): The date at which the data collection stops (stop NOT included).
    Returns:
        DataFrame: The dataframe with the events data over the time interval.
    """
    events = DataFrame()
    day = start
    while day <= stop:
        print(f"Retrieving {event_type} data for {day}")
        month = day.ctime()[4:7]
        day_str = "-".join([day.strftime("%Y"), month, day.strftime("%d")])
        resp = requests.get(
            url=f"https://aavefulldata.lab.groupe-genes.fr/events/{event_type}",
            params={"date": day_str},
            verify=False,
        )
        day_events = pd.json_normalize(resp.json())
        day_events["day"] = day
        events = pd.concat((events, day_events))
        day += timedelta(days=1)
    return events
