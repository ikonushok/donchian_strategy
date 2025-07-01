import os
import shutil

import yaml
import random
import datetime

import numpy as np

import optuna
import optuna.visualization as vis
import plotly.io as pio

from intra_channel_trading.auxiliary.utils import calculate_profit
from intra_channel_trading.scripts.config_loader import load_config
from intra_channel_trading.scripts.data_loader import load_data
from intra_channel_trading.scripts.strategy import donchian_rsi_exit_only


random.seed(42)
np.random.seed(42)

def evaluate_strategy(signals, params, destination_path, filename='result'):
    stats = calculate_profit(signals, verbose=False, filename=f"{destination_path}/{filename}", params=params)
    # print(f'\n{stats[:-3]}')
    return stats

def optuna_optimize_strategy(data, params, destination_path, n_trials=5):
    def objective(trial):
        signal_params = {
            'donchian_window': trial.suggest_int('donchian_window', 10, 50),
            'rsi_period': trial.suggest_int('rsi_period', 5, 30),
            'rsi_exit': trial.suggest_int('rsi_exit', 10, 50),
            'cooldown_bars': trial.suggest_int('cooldown_bars', 5, 50),
            'atr_enabled': True,
            'atr_period': trial.suggest_int('atr_period', 5, 30),
            'atr_threshold': trial.suggest_float('atr_threshold', 0.0001, 0.0015),
        }

        signals = donchian_rsi_exit_only(data.copy(), signal_params)
        stats = evaluate_strategy(signals, params, destination_path, filename=f"trial_{trial.number}")

        score = (
            stats['Return [%]'] * 0.4 +
            stats['Sharpe Ratio'] * 0.2 +
            stats['Win Rate [%]'] * 0.2 +
            stats['Profit Factor'] * 0.2 +
            stats['Expectancy [%]'] * 0.1 -
            stats['Max. Drawdown [%]'] * 0.5
        )
        return score

    study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials)

    return study



def main():
    source_config_path = "../configs/config_donchian_rsi.yaml"
    config = load_config(source_config_path)
    # Извлечение конфигурации для данных, стратегии и других параметров
    out_cfg = config.get('output', {})
    data_cfg = config.get('data', {})  # Данные теперь находятся под ключом 'data'
    dataset_path = data_cfg.get('dataset_path', '')  # Путь к папке с данными
    marketdata = data_cfg.get('marketdata', '')  # Имя файла данных

    strategy_cfg = config.get('strategy', {})
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

    ticker = marketdata.split('/')[-1].split('_')[0]
    timeframe = marketdata.split('/')[-1].split('_')[1]
    broker = marketdata.split('/')[-1].split('_')[4][:-4]
    print(ticker, timeframe, broker)

    now = datetime.datetime.now()
    add_on_to_folder_name = now.strftime("%Y%m%d%H%M%S")
    destination_path = f"../outputs/tune_outputs/tune_{ticker}_{timeframe}_{broker}_{add_on_to_folder_name}"
    os.makedirs(destination_path, exist_ok=True)

    # Загрузка данных
    data = load_data(f'../{dataset_path}/{marketdata}',
                     start_date=data_cfg["start_date"],
                     end_date=data_cfg["end_date"])

    study = optuna_optimize_strategy(data, params, destination_path, n_trials=5)
    # Сохраняем лучшие параметры как YAML
    # best_params_path = os.path.join(destination_path, "best_params.yaml")
    # with open(best_params_path, "w") as f:
    #     yaml.dump(study.best_trial.params, f, allow_unicode=True)

    # Заменяем параметры в конфиге
    optimized_config = config.copy()
    optimized_strategy_cfg = optimized_config['strategy']

    # Обновляем только существующие ключи
    for key, value in study.best_trial.params.items():
        if key in optimized_strategy_cfg:
            optimized_strategy_cfg[key] = value

    # Путь к новому конфигу
    optimized_config_path = os.path.join(destination_path, "optimized_config.yaml")
    with open(optimized_config_path, "w") as f:
        yaml.dump(optimized_config, f, allow_unicode=True, sort_keys=False)

    # Визуализация истории оптимизации
    opt_hist_fig = vis.plot_optimization_history(study)
    opt_hist_fig.show()
    pio.write_html(opt_hist_fig, file=os.path.join(destination_path, "opt_history.html"))

    # Визуализация важности параметров
    opt_param_fig = vis.plot_param_importances(study)
    opt_param_fig.show()
    pio.write_html(opt_param_fig, file=os.path.join(destination_path, "opt_param_importance.html"))

    print("Best Parameters:")
    for key, value in study.best_params.items():
        print(f"{key}: {value}")
    print(f"Best Score: {study.best_value:.4f}")


    # Генерация имени
    filename = (
        f"{ticker}_{timeframe}_{data_cfg.get('start_date')}-{data_cfg.get('end_date')}_signals_"
        f"dnch.w{study.best_params['donchian_window']}.rsi{study.best_params['rsi_period']}."
        f"rsiexit{study.best_params['rsi_exit']}.cld{study.best_params['cooldown_bars']}."
        f"atr{params['atr_enabled']}_source={broker}"
    )

    # Создание сигналов и расчет метрик
    final_signals = donchian_rsi_exit_only(data.copy(), study.best_params)
    final_stats = calculate_profit(
        signals=final_signals,
        verbose=True,
        filename=f"{destination_path}/{filename}",
        params=params  # здесь params — торговые настройки (fixed lot и т.д.)
    )
    # Сохранение результатов
    final_signals.to_csv(f"{destination_path}/{filename}.csv")
    final_stats[:-3].to_csv(f"{destination_path}/{filename}_stats.csv")
    final_stats._trades.to_csv(f"{destination_path}/{filename}_trades.csv")
    # Копирование конфигов
    shutil.copy2(source_config_path, f"{destination_path}/{os.path.basename(source_config_path)}")
    shutil.copy2(optimized_config_path, f"{destination_path}/{os.path.basename(optimized_config_path)}")
    # Печать критерия
    criteria = final_stats['Equity Final [$]'] - 100_000 - final_stats['# Trades'] * 7
    print(f"\n📌 Итоговый критерий: {criteria:.2f}")


if __name__ == "__main__":
    main()
