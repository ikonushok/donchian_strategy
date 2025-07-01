
import pandas as pd

# def load_data(data_path, start_date, end_date):
#     data = pd.read_csv(data_path, parse_dates=True, index_col="timestamp")
#     data = data[(data.index >= start_date) & (data.index <= end_date)]
#     return data

def load_data(file_path,
              start_date, end_date,
              verbose=False):
    df = pd.read_csv(file_path)
    df['Open'] = df['Open'].astype(float)
    df['High'] = df['High'].astype(float)
    df['Low'] = df['Low'].astype(float)
    df['Close'] = df['Close'].astype(float)
    # df['Datetime'] = df['Date'].str.replace('.', '-') + ' ' + df['Time'] + ':00'
    # df = df.drop(columns=['Date', 'Time'])
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.sort_values(by=['Datetime'])
    df.drop_duplicates(subset=['Datetime'], keep='first', inplace=True)
    df.set_index('Datetime', inplace=True)
    # Filter data by date
    dataset = df.copy()
    dataset = dataset[(dataset.index >= start_date) & (dataset.index <= end_date)]
    if verbose:
        dataset.plot(y='Close', use_index=True, title=f'Dataset from {start_date} to {end_date}')
        plt.show()
    return dataset