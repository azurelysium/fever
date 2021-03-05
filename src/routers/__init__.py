# pylint: disable=too-few-public-methods
from typing import Optional, Any

from pydantic import BaseModel


class RequestPayload(BaseModel):
    """Request Payload Base"""

    class Config:
        """BaseModel Config"""

        extra = "forbid"


class ResponsePayload(BaseModel):
    """Response Payload Base"""

    success: bool = False
    result: Optional[Any] = None
    message: Optional[str] = ""

    class Config:
        """BaseModel Config"""

        extra = "forbid"


class RouterException(Exception):
    """Exception raised in routers"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
