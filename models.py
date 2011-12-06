from peewee import *

db = SqliteDatabase("aiserver.db") # Could change.

class CustomModel(Model):
    class Meta:
        database = db

class User(CustomModel):
    username = TextField(unique=True)
    password = CharField()
    priv = IntegerField()
