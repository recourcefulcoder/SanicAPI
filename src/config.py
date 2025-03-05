import datetime
import logging
import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv


def load_environ():
    base_dir = Path(__file__).resolve().parent.parent
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        logging.warning(".env file not found")


load_environ()

SANIC_SECRET: Final = os.getenv("SANIC_SECRET")
WEBHOOK_SECRET: Final = os.getenv("WEBHOOK_SECRET")

POSTGRES_DB: Final = os.getenv("POSTGRES_DB")
POSTGRES_USER: Final = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: Final = os.getenv("POSTGRES_PASSWORD")
HOST: Final = os.getenv("HOST")

ACCESS_TOKEN_EXP_TIME: datetime.timedelta = datetime.timedelta(minutes=15)
