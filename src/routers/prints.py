from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi import Form, File, UploadFile
from PIL import Image

from common.constants import PrintType
from common.configuration import Config
from common.datastore import Database
from common.printer import Printer
from common.utils import get_local_isoformat
from routers import RouterException, RequestPayload, ResponsePayload

router = APIRouter()

def _print_header(
        config: Config,
        printer: Printer,
        print_id: str,
        username: str,
) -> None:
    if config["printer"]["printHeader"] == "true":
        printer.text(f"PRINT_ID: {print_id}\n")
        printer.text(f"USERNAME: {username}\n")
    printer.newline(int(config["printer"]["numLinefeeds"]))

def _print_footer(
        config: Config,
        printer: Printer,
) -> None:
    printer.newline(int(config["printer"]["numLinefeeds"]))
    if config["printer"]["printDivider"] == "true":
        n_columns = int(config["printer"]["textColumns"])
        printer.text(config["printer"]["dividerChar"] * n_columns)
    printer.newline(int(config["printer"]["numLinefeeds"]))

def _print_text(
        _config: Config,
        printer: Printer,
        content: str,
) -> None:
    printer.text(content)

def _print_image(
        config: Config,
        printer: Printer,
        image: Image,
) -> None:
    scale = float(config["printer"]["imageWidth"]) / image.width
    width, height = int(config["printer"]["imageWidth"]), int(image.height * scale)
    image_scaled = image.resize((width, height))
    printer.image(image_scaled, center=True)


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

# POST /prints/{print_id}
@router.post("/prints/{print_id}")
async def reprint(req: Request, print_id: str) -> ResponsePayload:
    """Re-print"""
    config = Config()
    database = Database()
    print_id = database.generate_print_id()
    username = req.state.user_info["username"]

    row = database.get_print(print_id)
    if not row:
        raise RouterException(f"Print not found ({print_id})")
    if row["username"] != username:
        raise RouterException(f"Print not owned by {username}")

    printer = Printer()
    _print_header(config, printer, print_id, username)

    if row["print_type"] == PrintType.TEXT.value:
        with open(row["artifact_path"], "r") as file_handle:
            content = file_handle.read()
        _print_text(config, printer, content)

    elif row["print_type"] == PrintType.IMAGE.value:
        img = Image.open(row["artifact_path"])
        _print_image(config, printer, img)

    _print_footer(config, printer)

    artifact_path = row["artifact_path"]
    database.add_print(
        username=username,
        print_id=print_id,
        print_type=PrintType(row["print_type"]),
        artifact_path=str(artifact_path),
        tags=row["tags"],
    )

    return ResponsePayload(
        success=True,
        result={
            "printId": print_id,
        },
    )


# POST /prints-new/text
class PrintTextRequest(RequestPayload):
    """Request Schema"""

    text: str
    tags: Optional[str]


@router.post("/prints-new/text")
async def print_text(req: Request, request: PrintTextRequest) -> ResponsePayload:
    """Print a text"""
    config = Config()
    database = Database()
    print_id = database.generate_print_id()
    username = req.state.user_info["username"]

    printer = Printer()
    _print_header(config, printer, print_id, username)
    _print_text(config, printer, request.text)
    _print_footer(config, printer)

    artifact_path = Path(config["server"]["artifactsDir"])
    artifact_path = artifact_path / f"{print_id}.txt"
    with artifact_path.open("w") as file_handle:
        file_handle.write(request.text)

    database.add_print(
        username=username,
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


# POST /prints-new/image
@router.post("/prints-new/image")
async def print_image(
        req: Request,
        image: UploadFile = File(...),
        tags: Optional[str] = Form(None),
) -> ResponsePayload:
    """Print an image"""
    config = Config()
    database = Database()
    print_id = database.generate_print_id()
    username = req.state.user_info["username"]

    printer = Printer()
    _print_header(config, printer, print_id, username)
    img = Image.open(image.file).convert("RGB")
    _print_image(config, printer, img)
    _print_footer(config, printer)

    artifact_path = Path(config["server"]["artifactsDir"])
    artifact_path = artifact_path / f"{print_id}.jpg"
    img.save(artifact_path)

    database.add_print(
        username=req.state.user_info["username"],
        print_id=print_id,
        print_type=PrintType.IMAGE,
        artifact_path=str(artifact_path),
        tags=tags if tags else "",
    )

    print('tags', tags)

    return ResponsePayload(
        success=True,
        result={
            "printId": print_id,
        },
    )
