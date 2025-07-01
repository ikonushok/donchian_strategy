import os
import datetime
import shutil

from auxiliary.utils import calculate_profit
from scripts.data_loader import load_data
from scripts.config_loader import load_config
from scripts.strategy import donchian_rsi_exit_only


def main():
    # Загрузка конфигурации
    source_config_path = "configs/config_donchian_rsi.yaml"
    config = load_config(source_config_path)

    # Извлечение конфигурации для данных, стратегии и других параметров
    out_cfg = config.get('output', {})
    data_cfg = config.get('data', {})  # Данные теперь находятся под ключом 'data'
    strategy_cfg = config.get('strategy', {})
    dataset_path = data_cfg.get('dataset_path', '')  # Путь к папке с данными
    marketdata = data_cfg.get('marketdata', '')  # Имя файла данных

    ticker = marketdata.split('/')[-1].split('_')[0]
    timeframe = marketdata.split('/')[-1].split('_')[1]
    broker = marketdata.split('/')[-1].split('_')[4][:-4]
    print(ticker, timeframe, broker)

    # Загрузка данных
    data = load_data(f'{dataset_path}/{marketdata}',
                     start_date=data_cfg["start_date"],
                     end_date=data_cfg["end_date"])
    # ---------- Пакет параметров для стратегии ----------
    params = {
        # -- основные индикаторы
        "donchian_window": strategy_cfg["donchian_window"],  # Donchian
        "rsi_period": strategy_cfg["rsi_period"],
        "rsi_exit": strategy_cfg["rsi_exit"],
        "cooldown_bars": strategy_cfg["cooldown_bars"],

        # -- управление торговой сессией
        "eod_exit": strategy_cfg["eod_exit"],
        "trading_hours": {
            "allowed": strategy_cfg["trading_hours"]["allowed"],
            "allowed_days": strategy_cfg["trading_hours"].get("allowed_days")
        },

        # -- ATR-фильтр волатильности
        "atr_enabled": strategy_cfg["atr_enabled"],
        "atr_period": strategy_cfg["atr_period"],
        "atr_threshold": strategy_cfg["atr_threshold"],
        "atr_pct_threshold": strategy_cfg.get("atr_pct_threshold"),
    }

    filename = (f"{ticker}_{timeframe}_{data_cfg.get('start_date')}-{data_cfg.get('end_date')}_signals_"
                f"dnch.w{params['donchian_window']}.rsi{params['rsi_period']}."
                f"rsiexit{params['rsi_exit']}.cld{params['cooldown_bars']}."
                f"eod{params['eod_exit']}.atr{params['atr_enabled']}"
                f"_source={broker}")
    print(filename)

    # Применение стратегии
    signals = donchian_rsi_exit_only(data, params)

    now = datetime.datetime.now()
    folder_name = now.strftime("%Y%m%d%H%M%S")
    destination = f"{out_cfg.get('destination_path', 'outputs')}/{folder_name}"
    os.makedirs(destination, exist_ok=True)

    # filename = f"{marketdata.split('.')[0]}"
    signals.to_csv(f"{destination}/{filename}.csv")

    # Рассчитываем статистику
    stats = calculate_profit(signals, verbose=True, filename=f"{destination}/{filename}", params=params)
    stats[:-3].to_csv(f"{destination}/{filename}_stats.csv")
    stats._trades.to_csv(f"{destination}/{filename}_trades.csv")
    shutil.copy2(source_config_path, f"{destination}/{os.path.basename(source_config_path)}")
    # Печать критерия
    criteria = stats['Equity Final [$]'] - 100_000 - stats['# Trades'] * 7
    print(f"Criteria: {criteria}")




if __name__ == "__main__":
    main()

