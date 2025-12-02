import json
from pathlib import Path
from logging import config


def load_looger(root_dir: Path) -> None:
    # log設定の読み込み
    log_config = Path.joinpath(root_dir, 'log', 'config.json')

    with open(log_config) as f:
        config.dictConfig(json.load(f))
