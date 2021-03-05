from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Request

from common.constants import PrintType
from common.configuration import Config
from common.datastore import Database
from common.printer import Printer
from common.utils import get_local_isoformat
from routers import RouterException, RequestPayload, ResponsePayload

router = APIRouter()


# GET /prints
@router.get("/prints")
async def get_print_history() -> ResponsePayload:
    """Get print history"""

    database = Database()
    rows = database.list_prints()

    config = Config()
    timezone = config["server"]["timezone"]

    result = []
    for row in rows:
        result.append(
            {
                "username": row["username"],
                "printId": row["print_id"],
                "printType": PrintType(row["print_type"]).name,
                "tags": row["tags"],
                "createdAt": get_local_isoformat(row["created_at"], timezone),
            }
        )

    return ResponsePayload(
        success=True,
        result=result,
    )


# GET /prints/{print_id}
@router.get("/prints/{print_id}")
async def get_print_info(print_id: str) -> ResponsePayload:
    """Get print information"""

    database = Database()
    row = database.get_print(print_id)
    if not row:
        raise RouterException(f"Print not found ({print_id})")

    config = Config()
    timezone = config["server"]["timezone"]

    return ResponsePayload(
        success=True,
        result={
            "username": row["username"],
            "printId": row["print_id"],
            "printType": PrintType(row["print_type"]).name,
            "tags": row["tags"],
            "createdAt": get_local_isoformat(row["created_at"], timezone),
        },
    )


# POST /prints-new/text
class PrintTextRequest(RequestPayload):
    """Request Schema"""

    text: str
    tags: Optional[str]


@router.post("/prints-new/text")
async def print_text(request: PrintTextRequest, req: Request) -> ResponsePayload:
    """Print a text"""
    printer = Printer()
    printer.text(request.text)

    config = Config()
    printer.newline(int(config["printer"]["numLinefeeds"]))

    database = Database()
    print_id = database.generate_print_id()

    artifact_path = Path(config["server"]["artifactsDir"])
    artifact_path = artifact_path / f"{print_id}.txt"
    with artifact_path.open("w") as file_handle:
        file_handle.write(request.text)

    database.add_print(
        username=req.state.user_info["username"],
        print_id=print_id,
        print_type=PrintType.TEXT,
        artifact_path=str(artifact_path),
        tags=request.tags if request.tags else "",
    )

    return ResponsePayload(
        success=True,
        result={
            "printId": print_id,
        },
    )
