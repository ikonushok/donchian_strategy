
import yaml

def load_config(path='config_donchian_rsi.yaml'):
    with open(path, 'r', encoding='utf-8') as f:  # Указываем кодировку 'utf-8'
        return yaml.safe_load(f)
