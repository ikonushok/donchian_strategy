
from scipy.optimize import minimize

def optimize_strategy(data, param_grid):
    def objective(params):
        # Функция для минимизации на основе backtest
        return backtest_score
    result = minimize(objective, initial_guess, bounds=param_grid)
    return result
