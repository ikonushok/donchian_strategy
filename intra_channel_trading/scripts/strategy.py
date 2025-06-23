
from tqdm import trange

from .indicators import calculate_donchian, calculate_rsi, calculate_atr


def donchian_rsi_exit_only(data, params):
    dataset = data.copy()

    # Применение RSI
    dataset = calculate_rsi(dataset, params.get('rsi_period'))
    # Применение Дончиан-каналов
    dataset = calculate_donchian(dataset, params.get('donchian_window'))

    # Логика торговли (покупка/продажа)
    # Применение ATR
    if params.get('atr_enabled'):
        dataset = calculate_atr(dataset, params.get('atr_period'))
        dataset.dropna(inplace=True)

        dataset['Signal'] = 1
        dataset['Entry'] = 0
        short, last_entry = False, -params.get('cooldown_bars')
        for i in trange(1, len(dataset)):
            price = dataset['Close'].iat[i]
            rsi = dataset['RSI'].iat[i]

            # Применение ATR для ограничения торговли в периоды низкой волатильности
            if dataset['ATR'].iat[i] < params.get('atr_threshold'):
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 0  # Торговля приостановлена (сигнал 0)
                continue

            # Enter short
            if (not short) and (i - last_entry >= params.get('cooldown_bars')) and price > dataset['Upper'].iat[i - 1]:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = -1
                dataset.iat[i, dataset.columns.get_loc('Entry')] = -1
                short = True
                last_entry = i
            # Exit short
            elif short and (price < dataset['Lower'].iat[i - 1] or rsi < params.get('rsi_exit')):
                short = False
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 1
            else:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = dataset['Signal'].iat[i - 1]
    else:
        # Инициализация: по умолчанию long
        dataset.dropna(inplace=True)
        dataset['Signal'] = 1
        short, last_entry = False, -params.get('cooldown_bars')
        for i in trange(1, len(dataset)):
            price = dataset['Close'].iat[i]
            rsi = dataset['RSI'].iat[i]
            # === ВХОД В ШОРТ === (временная позиция)
            if (not short) and (i - last_entry >= params.get('cooldown_bars')) and price > dataset['Upper'].iat[i - 1]:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = -1
                short = True
                last_entry = i
            # === ВЫХОД ИЗ ШОРТА === (возврат в лонг)
            elif short and (price < dataset['Lower'].iat[i - 1] or rsi < params.get('rsi_exit')):
                short = False  # снова в лонге (по умолчанию Signal остаётся 1)
            # === УДЕРЖАНИЕ СИГНАЛА ===
            else:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = dataset['Signal'].iat[i - 1]

    # EOD exit if enabled
    if params.get('eod_exit') and not params.get('eod_open'):
        # Применяем lags для заполнения сигнала до появления противоположного сигнала
        for i in trange(1, len(dataset)):
            current_time = dataset.index[i]
            signal = dataset['Signal'].iat[i]
            # Если текущее время >= 9, и сигнал равен 1 или -1, ставим его на 0
            if current_time.hour >= params.get('eod_exit_time') and signal != 0:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 0
                # print(f"Время {current_time}. Сигнал {signal} установлен в 0.")

    elif params.get('eod_exit') and params.get('eod_open'):
        position = None  # Запоминаем текущую позицию
        for i in trange(1, len(dataset)):
            current_time = dataset.index[i]
            signal = dataset['Signal'].iat[i]

            # 1. После eod_exit_time все сигналы становятся 0
            if current_time.hour >= params.get('eod_exit_time') and signal != 0:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 0  # Обнуляем сигнал
                # print(f"Время {current_time}. Сигнал {signal} установлен в 0.")

            # 2. В 00:00 запоминаем текущую позицию, если сигнал был != 0
            if current_time.hour == 0 and current_time.minute == 0:
                position = signal  # Сохраняем текущую позицию
                dataset.iat[i, dataset.columns.get_loc('Signal')] = 0  # Обнуляем сигнал
                # print(f"Время {current_time}. Позиция {position} сохранена.")

            # 3. После 00:00, если появляется противоположный сигнал, торговля возобновляется
            if position is not None and signal != 0 and signal != position:
                dataset.iat[i, dataset.columns.get_loc('Signal')] = signal  # Возобновляем торговлю
                position = None  # Сигнал сменился, сбрасываем позицию
                # print(f"Время {current_time}. Торговля возобновлена с сигналом {signal}.")

    return dataset
