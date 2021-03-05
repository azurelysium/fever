from typing import Optional, Any
from uuid import uuid4
import time

import dataset

from common.constants import PrintType
from common.patterns import singleton


@singleton
class Database:
    """Class for stroing print information"""

    def __init__(self) -> None:
        self.database: Optional[dataset.Database] = None

    def configure(self, database_uri: str) -> None:
        """Configure database object"""
        self.database = dataset.connect(database_uri)

    @staticmethod
    def generate_print_id(length: int = 10) -> str:
        """Generate hash-based print id"""
        return uuid4().hex[:length]

    def list_prints(self, limit: int = 30) -> Any:
        """Get the list of recent prints"""
        assert self.database
        return self.database["prints"].find(order_by=["-id"], _limit=limit)

    def get_print(self, print_id: str) -> Any:
        """Get detailed information of a print"""
        assert self.database
        return self.database["prints"].find_one(print_id=print_id)

    # pylint: disable=too-many-arguments
    def add_print(
        self,
        username: str,
        print_id: str,
        print_type: PrintType,
        artifact_path: str,
        tags: str = "",
    ) -> None:
        """Add new print information"""
        assert self.database
        table = self.database["prints"]
        row = dict(
            username=username,
            print_id=print_id,
            print_type=print_type.value,
            artifact_path=artifact_path,
            tags=tags,
            created_at=time.time(),
        )
        assert table.insert(row, ["print_id"]), "Insertion failed."
