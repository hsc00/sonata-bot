import os

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

db_path = os.getenv("SONATA_BOT_DB_PATH", "sonata.db")
db = SqliteExtDatabase("sonata.db", pragmas=(("journal_mode", "wal"),))

class BaseModel(Model):
    class Meta:
        database = db
