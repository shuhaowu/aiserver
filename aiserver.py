#The AI Server
#Copyright (C) 2011 Shuhao Wu

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


import SocketServer
import threading
import logging
from Queue import Queue
import random
import pdb
import socket

import auth
import models
import games
import games.tictactoe
import games.custom

HOST, PORT = "", 6055

class Pairer(threading.Thread):
    def __init__(self, readyUserQueue, server, gameClass):
        threading.Thread.__init__(self)
        self.readyUserQueue = readyUserQueue # TODO: URGENT: Remove users from queue when disconnected. (Perhaps extend Queue)
        self.server = server
        self.gameClass = gameClass
        self.daemon = True

    def getUser(self):
        while True:
            player = self.readyUserQueue.get()
            if not player.disconnected:
                return player

    def run(self):
        game = self.gameClass.name
        while True:
            players = (self.getUser(), self.getUser())
            while players[0].disconnected or players[1].disconnected:
                players = (self.getUser(), self.getUser())
            gameobj = self.gameClass(self.server, *players)
            self.server.onGoingGames[game].append(gameobj)
            for player in players:
                player.game = gameobj

            gameobj.start()

__version__ = "0.1b"

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M')
                    #filename="aiserver.log",
                    #filemode="a")

logger = logging.getLogger("aiserver")

class ClientHandler(SocketServer.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        self.running = False

    def handle(self):
        self.commands = commands = {
            "HELP" : self.help,
            "QUIT" : self.quit,
            "GAMES" : self.listGames,
            "VERSION" : self.showVersion,
            "JOIN" : self.joinGame,
            "READY" : self.ready,
            "USERS" : self.server.showUsers,
            "STATUS" : self.status
        }

        logger.info("Accepted client from: %s:%d" % self.client_address)
        self.send("Welcome to the AI server by Shuhao Wu. We have %d players on board.\nPlease authenticate now." % self.server.playercount())
        data = self.request.recv(1024)
        data = data.strip().split(" ")

        if len(data) < 2:
            logger.warning("Malformed data: %s" % str(data))
            self.sendStatus(403, "Authentication Failure")
        else:
            username = data[0]
            password = data[1]
            if username in self.server.clients:
                logger.warning("Client from %s:%d tried to login with '%s' while already logged in." % (self.client_address + (username, )))
                self.sendStatus(403, "User '%s' already on board." % username)
            elif auth.login(username, password):
                if auth.priv(username) >= 1: # Add admin functionalities
                    self.commands["SHUTDOWN"] = self.server.adminRequestShutdown

                self.username = username
                self.game = False
                self.gamemode = None
                self.readyStatus = False
                self.running = True
                self.disconnected = False

                self.sendStatus(200, "Welcome aboard, %s! Use 'HELP' to check all the available commands." % username)
                logger.info("Client from %s:%d authenticated." % self.client_address)

                self.server.onUserConnected(username, self)
                try:
                    while self.running:
                        try:
                            data = self.request.recv(1024)
                        except (socket.error, socket.timeout) as e:
                            self._socketError(e)
                            break

                        data = data.strip().split(" ")
                        logger.debug("Client %s:%d sent command: %s" % (self.client_address + (data[0], )))
                        if self.game and data[0] in self.game.commands:
                            callback = self.game.processCommand
                        else:
                            callback = commands.get(data[0], self.notAvailable)

                        if callback(self, *data):
                            break
                finally:
                    self.server.onUserDisconnected(self)
            else:
                logger.warning("Client from %s:%d failed to authenticate." % self.client_address)
                self.sendStatus(403, "Authentication Failure")

    def _socketError(self, e):
        logger.warning("Socket error from '%s': %s" % (self.username, str(e)))
        self.running = False
        self.server.onUserDisconnected(self)

    def ready(self, handler, *args):
        """Signals to the server that you're ready for pairing with another player.
    Note: After sending this command, the server will not send any data back to you until a game has been started. If your program is single threaded GUI, your interface may freeze.
    Note: You must be in a game mode first before signalling for READY"""
        self.readyStatus = True
        self.server.userReady(self)

    def status(self, handler, *args):
        """Shows the game mode that you're in and if you're in a game or not.
    Example: lobby 0 - You're in the lobby and not in a game
    Example: tictactoe foo - You're in the tictactoe game room and in a game with 'foo'
    Note: Different game will have different STATUS command syntax."""
        self.send(self.gamemode.name if self.gamemode else "lobby")

    def sendStatus(self, code, message):
        self.send("STATUS: %d\nMSG: %s" % (code, message))

    def send(self, message):
        try:
            self.request.send("%s\n" % message)
        except (socket.error, socket.timeout) as e:
            self._socketError(e)

    def notAvailable(self, handler, *args):
        self.sendStatus(404, "Command Not Available")

    def quit(self, handler, *args):
        """Properly quit the server."""
        # TODO: Broadcast
        return True

    def listCommands(self):
        s = ""
        for command in self.commands:
            s += " - %s\n" % command
        if self.game:
            for command in self.game.commands:
                s += " - %s\n" % command
        s += "To check help for a specific command, do HELP <commandname>"
        self.send(s)

    def help(self, handler, *args):
        """Display help message for each command.
    Example Usage: HELP QUIT - This will display the help message for the quit command
    Syntax: HELP [<command>]
    Note: This command is used for development purposes only."""
        if len(args) < 2:
            self.listCommands()
        else:
            if self.game and args[1] in self.game.commands:
                function = self.game.commands[args[1]]
            else:
                function = self.commands.get(args[1], None)

            if function is None:
                self.send("Command '%s' doesn't exists!" % args[1])
            else:
                self.send(function.__doc__)

    def listGames(self, handler, *args):
        """Lists all the available games (their unique names used for the JOIN command). Or list the help of a particular game if specified with a game name.
    Example: GAMES - list all games
    Example: GAMES tictactoe - List of help for the tictactoe game
    Syntax: GAMES [<name>]
    Note: This command is used for development purposes only."""
        if len(args) < 2:
            s = ""
            gamesinfo = self.server.listGamesAndShortDescription()
            for name in gamesinfo:
                s += "%s - %s\n" % (name, gamesinfo[name].split("\n")[0])
            self.send(s.strip())
        else:
            game = self.server.games.get(args[1], None)
            info = game.__doc__ if game else "Game '%s' doesn't exist!" % args[1]
            self.send(info)

    def malformedRequest(self, command):
        self.sendStatus(400, "Please refer to %s usage with HELP %s" % (command, command))

    def joinGame(self, handler, *args):
        """Join a game. This changes the game mode of a player on the server. If the player is already in a game mode and not in a game, this will change their game mode.
    Example Usage: JOIN tictactoe - Joins the tic tac toe game room.
    Syntax: JOIN <name>"""
        if self.game:
            self.sendStatus(403, "You cannot change mode while in a game.")
        else:
            if len(args) < 2:
                self.sendStatus(400, "Please refer to the JOIN usage with HELP JOIN")
            else:
                if args[1].lower() == "lobby":
                    self.gamemode = None
                    self.server.movePlayer(self.username, "lobby")
                    self.sendStatus(200, "Operation Successful")
                elif args[1] not in self.server.games:
                    self.sendStatus(404, "Game '%s' doesn't exist!" % args[1])
                else:
                    self.gamemode = self.server.games[args[1]]
                    self.server.movePlayer(self.username, args[1])
                    self.sendStatus(200, "Operation Successful")

    def showVersion(self, handler, *args):
        """ Shows the about message of the server """
        self.send("AI Server %s by Shuhao Wu" % __version__)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer): # Expecting a max of like 30 users. So Threading will suffice. Also trying to keep vanilla python
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.clients = {}
        self.numplayers = 0

        self.games = {}
        self.rooms = {"lobby" : []}

        self.readyUsersQueues = {}
        self.pairers = {}
        self.onGoingGames = {}
        self._hookGames()
        for game in self.games:
            self.readyUsersQueues[game] = Queue()
            self.pairers[game] = Pairer(self.readyUsersQueues[game], self, self.games[game])
            self.pairers[game].start()


    def showUsers(self, handler, *args):
        """Show all the users in the server if the player is in the lobby or all the players in the same game mode if the player is in a game mode"""
        users = []
        if handler.gamemode:
            for player in self.rooms[handler.gamemode]:
                users.append(player)
        else:
            for player in self.clients:
                users.append(player)
        handler.send(" ".join(users))

    def userReady(self, handler):
        if handler.gamemode is None:
            handler.sendStatus(400, "You need to join a game mode first.")
        else:
            self.readyUsersQueues[handler.gamemode.name].put(handler)
            logger.info("User %s is ready to be paired." % handler.username)

    def adminRequestShutdown(self, handler, *args):
        """Shutsdown the server. Admin only"""
        logger.warning("%s from %s:%d requested server shutdown. Complying..." % ((handler.username, ) + handler.client_address))
        handler.send("Complying with shutdown request. Terminating all %d users." % self.playercount())
        self.shutdown()

    def adminRequestPairing(self, handler, *args):
        handler.send("Disabled")
        return
        logger.info("%s requests game pairing to be commenced." % handler.username)
        for game in self.readyUsers:
            while len(self.readyUsers[game]) > 1:
                player1 = self.readyUsers[game].pop(random.choice(range(len(self.readyUsers[game]))))
                player2 = self.readyUsers[game].pop(random.choice(range(len(self.readyUsers[game]))))
                gameobj = self.games[game](self, player1, player2)
                self.onGoingGames[game].append(gameobj)
                player1.game = gameobj
                player2.game = gameobj
                gameobj.start()

    def endGame(self, room, game):
        self.onGoingGames[room].pop(self.onGoingGames[room].index(game))
        for player in game.players:
            player.game = None
            player.game = None
        logger.info("Game of %s between %s and %s ended." % (room, game.players[0].username, game.players[1].username))

    def handle_error(self, request, client_address):
        import traceback
        logger.error("Exception happened during processing of request from %s:%d" % client_address)
        logger.error(traceback.format_exc())

    def movePlayer(self, username, newroom):
        for room in self.rooms:
            if username in self.rooms[room]:
                self.rooms[room].remove(username)
                break
        self.rooms[newroom].append(username)

    def _addGame(self, gameClass):
        self.games[gameClass.name] = gameClass
        self.rooms[gameClass.name] = []
        self.onGoingGames[gameClass.name] = []

    def _hookGames(self):
        self._addGame(games.tictactoe.TicTacToe)
        self._addGame(games.custom.Custom)

    def playercount(self):
        return self.numplayers

    def listGamesAndShortDescription(self):
        d = {}
        print self.games
        for name in self.games:
            d[name] = self.games[name].shortDescription()
        return d

    def onUserConnected(self, username, handler):
        self.clients[username] = handler
        self.numplayers += 1
        self.rooms["lobby"].append(username)

    def _removeUser(self, d, username):
        for key in d:
            try:
                d[key].remove(username)
            except ValueError:
                pass

    def onUserDisconnected(self, user):
        username = user.username
        if user.game:
            user.game.connectionLost(username)
        self._removeUser(self.rooms, username)
        user.disconnected = True
        logger.info("Disconnected client from %s:%d" % user.client_address)
        if username in self.clients:
            del self.clients[username]
        else:
            logger.warning("Client %s was not tracked in global client list. Investigate? %s" % (username, str(self.clients)))
        self.numplayers -= 1

if __name__ == "__main__":
    server = ThreadedTCPServer((HOST, PORT), ClientHandler)
    models.db.connect()
    logger.info("AI Server is now running.")
    try:
        server.serve_forever()
    finally:
        logger.warning("Closing database")
        logger.warning("Server shutdown")
        models.db.close()
