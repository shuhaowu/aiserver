The AI Server
=============

The AI Server is a multiplayer game server (chat server) for 2 player games.
This server is designed to be very simple (non-standard communication
protocal, sorry folks).

Licensed under GPLv3, see LICENSE for details.

Note: This application embeds peewee for ease of use reasons, under peewee.py
The original source code (and the up to date copy) is available at
https://github.com/coleifer/peewee

Running
-------

The server is designed so that it doesn't depend on anything other than vanilla
python. It's been tested on Python 2.7 on Linux and Windows.

If you compiled Python, it must have threading enabled.

Run `python aiserver.py`

For test clients, go under the directory testclients... The tictactoeclient
requires PyGTK and Glade.


Default DB Username Passwords
-----------------------------
Some usernames and passwords that's available for use in the database that I've
included.

Regular user accounts:

    test /{l?U~>8l5-i<5oIfN?9
    testacc i6AgKTH+'=vEh<jZ5#;t
    test1 hello
    account0 Dll;ZHp[s,8co5%2j(Tb
    account1 t2#rxW)TPOE$78MN22mv
    account2 ;.)5oB1nLz!vv*Z.c<*'
    account3 [NfF3wPXl=z@6rVR9v4H
    account4 So;sQ^fW.K3uZ-dpKTA>
    account5 7UN42J4Ncxw)+g'WIy*m
    account6 ne-ql#mi/xWrL,9Og,fa
    account7 QoW2]mLR}bjZP}zs.dK-
    account8 5kl~1VEz3StY0WI<&V2W
    account9 &T%HrK1+7mkTC<Z^.2Wp

Here is an admin account:

    admin 7mZki#@90%0'fR)]di(H

To create an user, open up console and cd into the directory containing auth.py
(or just the root folder of the server).

Type `python` into the console.

    >>> import auth
    >>> auth.register("<username>")                     # 1
    "&T%HrK1+7mkTC<Z^.2Wp"
    >>> auth.register("<username>", "<password>")       # 2
    >>> auth.register("<username>", "<password>", 1)    # 3

The 1st line registers a user with the name <username> and returns the password.
The 2nd line registers a user with the name <username> and password <password>.
The 3rd line registers an admin with the name <username> and password <password>.

More info
---------

See `TECHNICAL_SPEC.markdown`
