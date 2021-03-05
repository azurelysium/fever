FEVER_SERVER_HOST ?= 127.0.0.1
FEVER_SERVER_PORT ?= 12345
FEVER_LOG_LEVEL ?= info
FEVER_COMMIT_HASH = `git rev-parse --short HEAD`

format:
	PYTHONPATH=src black src/

check:
	PYTHONPATH=src pytest -s -v --pylint --flake8 --mypy src/

run:
	PYTHONPATH=src uvicorn --host ${FEVER_SERVER_HOST} --port ${FEVER_SERVER_PORT} --log-level ${FEVER_LOG_LEVEL} --reload src.main:app

build:
	docker build -t azurelysium/fever:latest -t azurelysium/fever:${FEVER_COMMIT_HASH} .

buildx:
	docker buildx build --platform linux/arm/v7 --build-arg BASE_IMAGE=arm32v7/python --load \
	       -t azurelysium/fever:armv7-latest -t azurelysium/fever:armv7-${FEVER_COMMIT_HASH} .

user:
	PYTHONPATH=src python -c 'from getpass import getpass; from common.utils import generate_user_entry; username = input("Username: "); password = getpass("Password: "); print(generate_user_entry(username, password))'
