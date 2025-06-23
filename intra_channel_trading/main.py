import os
from auxiliary.utils import calculate_profit, load_data
from scripts.config_loader import load_config
from scripts.strategy import donchian_rsi_exit_only


def main():
    # Загрузка конфигурации
    config = load_config("configs/config_donchian_rsi.yaml")

    # Извлечение конфигурации для данных, стратегии и других параметров
    out_cfg = config.get('output', {})
    data_cfg = config.get('data', {})  # Данные теперь находятся под ключом 'data'
    strategy_cfg = config.get('strategy', {})
    # Формируем полный путь к данным
    dataset_path = data_cfg.get('dataset_path', '')  # Путь к папке с данными
    marketdata = data_cfg.get('marketdata', '')  # Имя файла данных
    if not dataset_path or not marketdata:
        raise ValueError("Некорректный путь или имя файла данных в конфиге.")
    data_file_path = os.path.join(dataset_path, marketdata)

    ticker = marketdata.split('/')[-1].split('_')[0]
    timeframe = marketdata.split('/')[-1].split('_')[1]
    broker = marketdata.split('/')[-1].split('_')[4][:-4]
    print(ticker, timeframe, broker)

    # Загрузка данных
    data = load_data(data_file_path, data_cfg['start_date'], data_cfg['end_date'])
    params = {
        'donchian_window': strategy_cfg['donchian_window'],
        'rsi_period': strategy_cfg['rsi_period'],
        'rsi_exit': strategy_cfg['rsi_exit'],
        'cooldown_bars': strategy_cfg['cooldown_bars'],
        'eod_exit': strategy_cfg['eod_exit'],
        'eod_exit_time': strategy_cfg['eod_exit_time'],
        'eod_open': strategy_cfg['eod_change_signal_open'],
        'atr_enabled': strategy_cfg['atr_enabled'],
        'atr_period': strategy_cfg['atr_period'],
        'atr_threshold': strategy_cfg['atr_threshold']
    }

    filename = (f"{ticker}_{timeframe}_{data_cfg.get('start_date')}-{data_cfg.get('end_date')}_signals_"
                f"dnch.w{params['donchian_window']}.rsi{params['rsi_period']}."
                f"rsiexit{params['rsi_exit']}.cld{params['cooldown_bars']}."
                f"eod{params['eod_exit']}.atr{params['atr_enabled']}"
                f"_source={broker}")
    print(filename)

    # Применение стратегии
    signals = donchian_rsi_exit_only(data, params)

    # Сохранение результатов
    destination = out_cfg.get('destination_path', 'outputs')
    os.makedirs(destination, exist_ok=True)

    # filename = f"{marketdata.split('.')[0]}"
    signals.to_csv(f"{destination}/{filename}.csv")

    # Рассчитываем статистику
    stats_rsi = calculate_profit(signals, verbose=True, filename=f"{destination}/{filename}")
    stats_rsi[:27].to_csv(f"{destination}/{filename}_stats.csv")
    stats_rsi._trades.to_csv(f"{destination}/{filename}_trades.csv")

    # Печать критерия
    criteria = stats_rsi['Equity Final [$]'] - 100_000 - stats_rsi['# Trades'] * 7
    print(f"Criteria: {criteria}")




if __name__ == "__main__":
    main()

