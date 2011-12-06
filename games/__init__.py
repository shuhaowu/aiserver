class Game(object):
    def __init__(self, server, *players):
        self.players = players
        self.server = server
        self.commands = {}
        self.brokenConnection = None

    def connectionLost(self, username):
        self.brokenConnection = username

    def processCommand(self, handler, *args):
        if self.brokenConnection:
            for player in self.players:
                if player.username != self.brokenConnection:
                    player.send("CONNECTION_BROKEN")
            return

        cmd = args[0]
        return self.commands.get(cmd, handler.notAvailable)(handler, *args)

    def start(self):
        raise NotImplementedError

    def opponent(self, me, username=True):
        for i in xrange(2):
            if me.username == self.players[i].username:
                if username:
                    return self.players[int(not i)].username
                else:
                    return self.players[int(not i)]

    @staticmethod
    def shortDescription():
        return "Description not available"
