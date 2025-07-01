import enum
from backtesting import Strategy


class SignalType(enum.IntEnum):
    long_signal = 1
    short_signal = -1
    exit_signal = 0
    no_changes = 2


def is_changed_signal(prev, current):
    return prev != current


class StrategyFixLot(Strategy):
    # Параметры стратегии
    donchian_window = None
    rsi_period = None
    rsi_exit = None
    cooldown_bars = None
    atr_enabled = None
    atr_period = None
    atr_threshold = None
    atr_pct_threshold = None

    eod_exit = False
    trading_hours = {'allowed': [[0, 24]], 'allowed_days': [0, 1, 2, 3, 4, 5, 6]}
    allowed_days = [0, 1, 2, 3, 4, 5, 6]

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self.signal = None

        # Безопасное извлечение allowed_days из trading_hours
        if self.trading_hours is None:
            self.trading_hours = {'allowed': [[0, 24]], 'allowed_days': [0, 1, 2, 3, 4, 5, 6]}
        self.allowed_days = self.trading_hours.get('allowed_days', [0, 1, 2, 3, 4, 5, 6])

    def init(self):
        self.signal = self.I(lambda x: x, self.data.df['Signal'])

    def is_trading_allowed(self):
        current_time = self.data.index[-1]
        current_hour = current_time.hour
        for start, end in self.trading_hours['allowed']:
            if start <= current_hour < end:
                return True
        return False

    def is_day_allowed(self):
        current_day = self.data.index[-1].weekday()
        return current_day in self.allowed_days

    def next(self):
        if len(self.signal) < 2:
            return

        previous_signal = int(self.signal[-2])
        last_signal = int(self.signal[-1])
        signal_sample = last_signal if is_changed_signal(previous_signal, last_signal) else SignalType.no_changes

        lot_size = 100_000
        trading_allowed = self.is_trading_allowed()
        day_allowed = self.is_day_allowed()

        # === eod_exit включён: запрещены действия вне времени и дней ===
        if self.eod_exit and (not trading_allowed or not day_allowed):
            if signal_sample in [SignalType.long_signal, SignalType.short_signal, SignalType.exit_signal]:
                self.position.close()  # можно только выйти
            return

        # === обычная логика входа/выхода ===
        if signal_sample == SignalType.long_signal:
            if not self.position.is_long:
                self.position.close()
                self.buy(size=lot_size)
        elif signal_sample == SignalType.short_signal:
            if not self.position.is_short:
                self.position.close()
                self.sell(size=lot_size)
        elif signal_sample == SignalType.exit_signal:
            self.position.close()
