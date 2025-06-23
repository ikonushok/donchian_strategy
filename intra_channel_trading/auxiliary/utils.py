import os
import yaml
import warnings

import pandas as pd
import matplotlib.pyplot as plt

from backtesting import Backtest
from backtesting import _plotting as plt_backtesting
from .backtest_strategy import Strategy_Fix_Lot

warnings.filterwarnings("ignore")
plt_backtesting._MAX_CANDLES = 1_000_000
pd.set_option("display.precision", 5)
pd.set_option("expand_frame_repr", False)


def load_data(file_path,
              start_date, end_date,
              verbose=False):
    df = pd.read_csv(file_path)
    # print(df)
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
    # print(df)
    # Filter data by date
    dataset = df.copy()
    dataset = dataset[(dataset.index >= start_date) & (dataset.index <= end_date)]
    if verbose:
        dataset.plot(y='Close', use_index=True, title=f'Dataset from {start_date} to {end_date}')
        plt.show()
    return dataset


def calculate_profit(signals,
                     verbose=False, filename=None):
    bt = Backtest(signals,
                  # strategy=Strategy_Cumulative,
                  strategy=Strategy_Fix_Lot,
                  cash=100_000,
                  margin=1 / 100,
                  commission=0.00,
                  exclusive_orders=True,
                  trade_on_close=False,
                  )
    stats = bt.run()

    if verbose:
        bt.plot(relative_equity=False,
                plot_equity=True,
                plot_drawdown=True,
                filename=f'{filename}.html')
        print(f'\n{stats[:27]}')
        print(f'\n{stats._trades}')

    return stats

def save_best_artifacts(ticker, timeframe, start_date, end_date, n_trials, best_trials, df_study,
                        buy_signals, sell_signals):

    best_trial = best_trials[0]
    best_trial.params['train_start_date'] = start_date
    best_trial.params['train_end_date'] = end_date
    best_trial.params['ticker'] = ticker
    best_trial.params['timeframe'] = timeframe
    best_trial.params['n_trials'] = n_trials
    best_trial.params['buy_signals'] = buy_signals
    best_trial.params['sell_signals'] = sell_signals
    print(f'\nBest_trial: {best_trial.params}\n')

    filename = (f"{ticker}_{timeframe}_{start_date}-{end_date}_wind{best_trial.params['window']}_"
                f"buy_{buy_signals}_sell_{sell_signals}")
    if not os.path.exists(f'outputs/trials/{filename}'):
        os.makedirs(f'outputs/trials/{filename}')

    df_study.to_csv(f'outputs/trials/{filename}/df_study_{filename}.csv')
    with open(f'outputs/trials/{filename}/best_trial_{filename}.yaml', 'w') as f:
        yaml.dump(best_trial.params, f, default_flow_style=False, sort_keys=False)
