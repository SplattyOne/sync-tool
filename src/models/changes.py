import enum
import json
from dataclasses import dataclass, asdict


class OperationEnum(str, enum.Enum):
    DEL_DIR = 'delete_directory'
    DEL_FILE = 'delete_file'
    ADD_DIR = 'add_dir'
    ADD_FILE = 'add_file'


@dataclass
class ChangeItem:
    operation: OperationEnum
    path: float
    b64content: str | None = None


def convert_to_json(changes: list[ChangeItem]) -> str:
    return json.dumps(list(map(lambda x: asdict(x), changes)), ensure_ascii=False)
