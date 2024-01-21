import logging
import logging.config
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from _typeshed import StrPath


def setup_logging(path: "StrPath" = "log.yaml"):
    path = Path(path)
    if path.exists():
        f = path.read_text()
        try:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        except Exception as e:
            raise e
