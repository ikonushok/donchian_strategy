from tqdm import trange
from .indicators import calculate_donchian, calculate_rsi, calculate_atr


def donchian_rsi_exit_only(data, params):
    dataset = data.copy()

    # Применение RSI
    dataset = calculate_rsi(dataset, params.get('rsi_period'))
    # Применение Дончиан-каналов
    dataset = calculate_donchian(dataset, params.get('donchian_window'))

    if params.get('atr_enabled'):
        dataset = calculate_atr(dataset, params.get('atr_period'))
        dataset.dropna(inplace=True)

        dataset['Signal'] = 1
        dataset['Entry'] = 0
        short, last_entry = False, -params.get('cooldown_bars')
        for i in trange(1, len(dataset)):
            price = dataset['Close'].iat[i]
            rsi = dataset['RSI'].iat[i]

            if dataset['ATR'].iat[i] < params.get('atr_threshold'):
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 0
                continue

            if (not short) and (i - last_entry >= params.get('cooldown_bars')) and price > dataset['Upper'].iat[i - 1]:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = -1
                dataset.iat[i, dataset.columns.get_loc('Entry')] = -1
                short = True
                last_entry = i
            elif short and (price < dataset['Lower'].iat[i - 1] or rsi < params.get('rsi_exit')):
                short = False
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 1
            else:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = dataset['Signal'].iat[i - 1]

    else:
        dataset.dropna(inplace=True)
        dataset['Signal'] = 1
        short, last_entry = False, -params.get('cooldown_bars')
        for i in trange(1, len(dataset)):
            price = dataset['Close'].iat[i]
            rsi = dataset['RSI'].iat[i]

            if (not short) and (i - last_entry >= params.get('cooldown_bars')) and price > dataset['Upper'].iat[i - 1]:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = -1
                short = True
                last_entry = i
            elif short and (price < dataset['Lower'].iat[i - 1] or rsi < params.get('rsi_exit')):
                short = False
            else:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = dataset['Signal'].iat[i - 1]

    return dataset

