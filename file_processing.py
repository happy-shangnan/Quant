import pandas as pd
import numpy as np
from binance.client import Client
from datetime import timedelta
import os
import logging

def interval_to_timedelta(interval):
    """Convert Binance interval string to a timedelta object."""
    unit = interval[-1]
    amount = int(interval[:-1])

    if unit == 'm':
        return timedelta(minutes=amount)
    elif unit == 'h':
        return timedelta(hours=amount)
    elif unit == 'd':
        return timedelta(days=amount)
    elif unit == 'w':
        return timedelta(weeks=amount)
    elif unit == 'M':
        # Note: timedelta does not support months; handle months separately if needed
        return timedelta(days=30 * amount)
    else:
        raise ValueError(f"Unsupported interval: {interval}")


def fetch_initial_data(client, symbol, interval, start_date, end_date, file_name):
    """Fetch initial historical data and save it to a CSV file."""
    klines = client.get_historical_klines(symbol, interval, start_date, end_date)

    # Updated columns to include open, high, low, close, and volume
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Selecting relevant columns
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    df.to_csv(file_name)
    print(f"Initial historical data saved to '{file_name}'")

    return df


def load_data(file_name):
    """Load existing data from a CSV file."""
    return pd.read_csv(file_name, index_col='timestamp', parse_dates=True)


def update_data(client, df, symbol, interval, file_name):
    """Fetch new data and update the CSV file."""
    latest_timestamp = df.index[-1]
    interval_delta = interval_to_timedelta(interval)
    latest_timestamp_plus_one = latest_timestamp + interval_delta  # Add the interval
    new_klines = client.get_historical_klines(symbol, interval,
                                              latest_timestamp_plus_one.strftime("%d %b, %Y %H:%M:%S"), "now UTC")

    # Updated columns to include open, high, low, close, and volume
    new_df = pd.DataFrame(new_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])

    new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms')
    new_df.set_index('timestamp', inplace=True)

    # Selecting relevant columns
    new_df = new_df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    # Concatenate and sort by timestamp, then remove duplicates
    df = pd.concat([df, new_df]).sort_index()
    df = df[~df.index.duplicated(keep='last')]

    df.to_csv(file_name)
    logging.info(f"Updated historical data saved to '{file_name}'")

    return df

