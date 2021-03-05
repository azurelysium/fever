import json
import os
from typing import Optional, Any, List, Dict, Tuple

from common.patterns import singleton


def _get_env_vars(
    obj: Dict[Any, Any], prefix: str, keys: List[str]
) -> List[Tuple[str, List[str]]]:
    if isinstance(obj, str):
        return [("_".join([prefix.upper()] + [key.upper() for key in keys]), keys)]
    env_vars = []
    for key in obj.keys():
        env_vars.extend(_get_env_vars(obj[key], prefix, keys + [key]))
    return env_vars


@singleton
class Config(dict):  # type: ignore
    """Configuration management class"""

    prefix = "FEVER"

    def __init__(self, path: Optional[str] = None) -> None:
        super().__init__()
        if path is None:
            path_ = os.environ.get(f"{self.prefix}_CONFIG_JSON", "./config.json")
        else:
            path_ = path
        self.load(path_)

    def reload(self) -> None:
        """Reload configuration from a file"""
        self.load(self.path)

    def _update_nested(self, keys: List[str], value: Any, target: Any = None) -> None:
        if target is None:
            target = self

        if len(keys) == 1:
            target[keys[0]] = value
            return

        if keys[0] not in target:
            target[keys[0]] = {}

        self._update_nested(keys[1:], value, target[keys[0]])

    def load(self, path: str) -> None:
        """Load configuration from a file"""
        self.clear()
        with open(path, "r") as file_handle:
            super().__init__(json.load(file_handle))
            self.path = path

        # override values when the environment variable is set
        # e.g.
        # env_vars = [
        #   ("FEVER_ESCPOS_FILE", lambda val: {"escpos": {"file": val}}),
        # ]
        # NOTE: all leaf nodes' type should be str

        env_vars = _get_env_vars(self, self.prefix, [])
        for var_name, keys in env_vars:
            if var_name in os.environ:
                self._update_nested(keys, os.environ[var_name])

    def save(self) -> None:
        """Save configuration to a file"""
        with open(self.path, "w") as file_handle:
            json.dump(self, file_handle)
