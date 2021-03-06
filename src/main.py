from base64 import b64decode
import logging
from pathlib import Path
from pprint import pprint

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.configuration import Config
from common.datastore import Database
from common.printer import Printer
from common.utils import validate_password
from routers import RouterException, ResponsePayload
from routers import prints


# Server settings
logger = logging.getLogger("main")


def _configure_app() -> None:
    config = Config()
    if config["server"]["printConfigOnStartup"] == "true":
        pprint(config)

    printer = Printer()
    printer.configure(config["printer"]["file"])

    database = Database()
    database.configure(config["server"]["databaseUri"])
    database.database["prints"].upsert({"print_id": "dummy"}, ["print_id"])
    database.database["prints"].delete(print_id="dummy")
    database.database["prints"].create_index(["print_id"])

    artifacts_dir_path = Path(config["server"]["artifactsDir"])
    artifacts_dir_path.mkdir(exist_ok=True)


# FastAPI app
_configure_app()
app = FastAPI(
    title="fever",
    description="simple thermal-printing server",
    version="0.0.1",
)


# Handlers
def _authenticate_user(username: str, password: str) -> bool:
    # load passwords file
    config = Config()
    if "users" not in config["server"]:
        config["server"]["users"] = {}
        with open(config["server"]["passwordsFile"], "r") as file_handle:
            for line in file_handle.readlines():
                file_username, file_password_hash = line.rstrip().split(":")
                config["server"]["users"][file_username] = file_password_hash

    if username == "anonymous" and config["server"]["anonymousLoginEnabled"] == "true":
        return True

    users = config["server"]["users"]
    if username not in users:
        return False
    if not validate_password(password, users[username]):
        return False
    return True


@app.middleware("http")
async def authentication_handler(request: Request, call_next):  # type: ignore
    """Authenticate user using BasicAuth"""
    username = "anonymous"
    password = "anonymous"
    if "authorization" in request.headers:
        header = request.headers["authorization"]
        if header.startswith("Basic "):
            b64encoded = header.replace("Basic ", "")
            try:
                decoded = b64decode(b64encoded).decode()
                username, password = decoded.split(":")
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(exc)

    if not _authenticate_user(username, password):
        response = ResponsePayload(
            success=False,
            message="Authentication failed.",
        )
        return JSONResponse(status_code=401, content=response.dict())

    request.state.user_info = {
        "username": username,
        "password": password,
    }

    response = await call_next(request)
    return response


@app.exception_handler(RouterException)
async def router_exception_handler(
    _request: Request, exc: RouterException
) -> JSONResponse:
    """Handle RouterException"""
    response = ResponsePayload(
        success=False,
        message=exc.message,
    )
    return JSONResponse(status_code=200, content=response.dict())


# Routers
app.include_router(prints.router, tags=["prints"])
