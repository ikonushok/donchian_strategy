
import os
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path


def load_trades(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["EntryTime"])
    if "PnL" not in df.columns:
        raise ValueError("Файл trade-логов должен содержать колонку PnL")
    df["EntryHour"] = df["EntryTime"].dt.hour
    return df.sort_values("EntryTime")


def save_hourly_stats(df: pd.DataFrame, out_csv: str) -> pd.DataFrame:
    hourly = (df.groupby("EntryHour")["PnL"]
                .agg(Trades="count", TotalPnL="sum", AvgPnL="mean")
                .reset_index()
                .sort_values("EntryHour"))
    hourly.to_csv(out_csv, index=False)
    print(f"hourly stats → {out_csv}")
    return hourly

def bar_plot(hourly: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=hourly["EntryHour"], y=hourly["TotalPnL"], name="Total PnL per Hour")
    fig.update_layout(title="Total PnL vs Entry Hour",
                      xaxis_title="Entry Hour (UTC)",
                      yaxis_title="Total PnL [$]")
    return fig

def equity_curves_by_hour(df: pd.DataFrame, save_path: str = None) -> go.Figure:
    fig = go.Figure()
    for h in range(24):
        chunk = df[df["EntryHour"] == h].copy()
        if chunk.empty:
            continue
        chunk["Equity"] = chunk["PnL"].cumsum()
        fig.add_scatter(x=chunk.index, y=chunk["Equity"],
                        mode="lines", name=f"Hour {h}", line=dict(width=1))
    df["Equity"] = df["PnL"].cumsum()
    fig.add_scatter(x=df.index, y=df["Equity"],
                    mode="lines", name="Total Equity", line=dict(width=2))
    fig.update_layout(title="Equity Curves by Entry Hour (with Total)",
                      xaxis_title="Trade index",
                      yaxis_title="Cumulative PnL [$]",
                      legend_title="Entry Hour / Total")
    if save_path:
        fig.write_html(save_path)

    return fig


def equity_curves_by_day(df: pd.DataFrame, save_path: str = None) -> go.Figure:

    fig = go.Figure()
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df["EntryDay"] = df["EntryTime"].dt.dayofweek

    for d in range(7):
        chunk = df[df["EntryDay"] == d].copy()
        if chunk.empty:
            continue
        chunk["Equity"] = chunk["PnL"].cumsum()
        fig.add_scatter(x=chunk.index, y=chunk["Equity"],
                        mode="lines", name=day_labels[d], line=dict(width=1))

    df["Equity"] = df["PnL"].cumsum()
    fig.add_scatter(x=df.index, y=df["Equity"],
                    mode="lines", name="Total Equity", line=dict(width=2))

    fig.update_layout(title="Equity Curves by Day of Week (with Total)",
                      xaxis_title="Trade index",
                      yaxis_title="Cumulative PnL [$]",
                      legend_title="Day of Week / Total")

    if save_path:
        fig.write_html(save_path)

    return fig


def main():
    source_path = Path('../outputs/tune_outputs/tune_EURGBP_5M_MetaQuotes-Demo_20250701203327/')
    destination_path = Path('../outputs/analytical_results')
    trades_file = ('EURGBP_5M_2025-01-04-2025-05-28_signals_dnch.w28.rsi25.rsiexit18.cld28.atrTrue_source=MetaQuotes-Demo_trades.csv')
    destination_path.mkdir(exist_ok=True)

    trades_path = source_path / trades_file
    trades = load_trades(trades_path)

    # visualize_and_save(trades, destination_path)
    hourly_stats_path = destination_path / trades_file.replace("_trades.csv", "_hourly_stats.csv")
    save_hourly_stats(trades, str(hourly_stats_path))
    # bar_plot(hourly).show()
    equity_curves_by_day(
        trades, save_path=destination_path / trades_file.replace("_trades.csv", "_equity_by_day.html")
    ).show()
    equity_curves_by_hour(
        trades, save_path=destination_path / trades_file.replace("_trades.csv", "_equity_by_hour.html")
    ).show()


if __name__ == "__main__":
    main()
