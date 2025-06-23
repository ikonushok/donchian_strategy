import enum
from backtesting import Strategy


class SignalType(enum.IntEnum):
    long_signal = 1
    short_signal = -1
    exit_signal = 0
    no_changes = 2

def is_changed_signal(prev, current):
    return prev != current


def is_risky():
    return False


class Strategy_Fix_Lot(Strategy):
    """
      Стратегия для тестирования сигналов НС
      Торговля на ФИКСИРОВАННУЮ сумму
      Подойдет для акций и BTC, где нет клиринга
    """

    def __init__(self, broker, data, params):
        super().__init__(broker, data, params)
        self.signal = None

    def init(self):
        self.signal = self.I(lambda x: x, self.data.df.Signal, name='Signal', overlay=False)

    def next(self):
        """
        Проход по всем барам
        """
        previous_signal = int(self.signal[-2])
        last_signal = int(self.signal[-1])
        last_price = self.data.Close[-1]

        signal_sample = last_signal if is_changed_signal(previous_signal, last_signal) else 2

        # Размер лота всегда фиксирован
        lot_size = 100_000  # Фиксированный размер лота

        if signal_sample == SignalType.long_signal:
            if not self.position.is_long:  # Если нет длинной позиции
                self.buy(size=lot_size)  # Покупаем 1 лот

        elif signal_sample == SignalType.short_signal:
            if not self.position.is_short:  # Если нет короткой позиции
                self.sell(size=lot_size)  # Продаем 1 лот

        elif signal_sample == SignalType.exit_signal:
            self.position.close()  # Закрыть позицию

