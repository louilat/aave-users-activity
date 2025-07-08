import pandas as pd
import numpy as np
from pandas import DataFrame
import json
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
    return events.drop_duplicates()


def collect_reserves_data(start: datetime, stop: datetime) -> DataFrame:
    """
    Collect the pool-level data from the api endpoint for a given time interval.
    Args:
        start (datetime): The date at which the data collection starts.
        stop (datetime): The date at which the data collection stops (stop NOT included).
    Returns:
        DataFrame: The dataframe with the reserves data over the interval.
    """
    reserves = DataFrame()
    day = start
    while day <= stop:
        print(f"Retrieving reserves data for {day}")
        month = day.ctime()[4:7]
        day_str = "-".join([day.strftime("%Y"), month, day.strftime("%d")])
        resp = requests.get(
            url="https://aavefulldata.lab.groupe-genes.fr/reserves",
            params={"date": day_str},
            verify=False,
        )
        day_reserves = pd.json_normalize(resp.json())
        day_reserves["day"] = day
        reserves = pd.concat((reserves, day_reserves))
        day += timedelta(days=1)
    return reserves


def collect_prices_data(start: datetime, stop: datetime) -> DataFrame:
    """
    Collect the pool-level data from the api endpoint for a given time interval.
    Args:
        start (datetime): The date at which the data collection starts.
        stop (datetime): The date at which the data collection stops (stop NOT included).
    Returns:
        DataFrame: The dataframe with the ETH prices data over the interval.
    """
    prices = DataFrame()
    day = start
    while day <= stop:
        print(f"Retrieving prices data for {day}")
        month = day.ctime()[4:7]
        day_str = "-".join([day.strftime("%Y"), month, day.strftime("%d")])
        resp = requests.get(
            url="https://aavefulldata.lab.groupe-genes.fr/prices",
            params={"date": day_str},
            verify=False,
        )
        day_reserves = pd.json_normalize(resp.json())
        day_reserves["day"] = day
        prices = pd.concat((prices, day_reserves))
        day += timedelta(days=1)
    return prices
