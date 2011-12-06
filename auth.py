import sqlite3
import hashlib
import models
from random import choice
import string

valid = string.letters + string.digits + "!@~#$%^&*()-=+_[{}]';.,<>/?'"

def login(username, password):
    hashedPass = hashlib.sha1(password).hexdigest() # Even though stored hashed, still just use some random string as you'll put it into a program
    return models.User.select().where(username=username, password=hashedPass).exists()

def priv(username):
    q = models.User.select().where(username=username)
    for u in q:
        return u.priv

def genpass(length=20):
    p = ""
    for i in xrange(length):
        p += choice(valid)
    return p

def register(username, p=None, priv=0):
    if p is None:
        password = genpass()
    else:
        password = p

    if " " in username or " " in password:
        return False

    hashedPass = hashlib.sha1(password).hexdigest()
    newuser = models.User.create(username=username, password=hashedPass, priv=priv)
    newuser.save()
    if p is None:
        return password
    return True
