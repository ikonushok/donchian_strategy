
import pandas as pd

def load_data(data_path, start_date, end_date):
    data = pd.read_csv(data_path, parse_dates=True, index_col="timestamp")
    data = data[(data.index >= start_date) & (data.index <= end_date)]
    return data
