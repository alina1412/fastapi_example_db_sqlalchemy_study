import datetime
import logging
from os import environ

import pytz
from dotenv import load_dotenv

load_dotenv()
key = environ.get("key")
assert key

db_settings = {
    "db_name": environ.get("DB_NAME"),
    "db_host": environ.get("DB_HOST"),
    "db_user": environ.get("DB_USERNAME"),
    "db_port": int(environ.get("DB_PORT")),
    "db_password": environ.get("DB_PASSWORD"),
    "db_driver": environ.get("DB_DRIVER"),
}


def utcnow() -> datetime:
    """datetime object with timezone awareness"""
    now: datetime = datetime.datetime.now(tz=pytz.utc)
    return now


logging.basicConfig(
    filename="logs.log",
    level=logging.WARNING,
    format="""[%(asctime)s] {%(filename)s:%(lineno)d} 
                        %(levelname)s - %(message)s""",
    datefmt="%H:%M:%S",  # datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)
