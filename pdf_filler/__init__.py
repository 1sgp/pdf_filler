from .const import VERSION
from yaml import safe_load

try:
    with open('config.yml', 'r') as f:
        conf = safe_load(f)
except BaseException as e:
    print(f'Cannot init cause of missing config.yml \n {e}')