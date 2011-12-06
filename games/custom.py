from games import Game
import logging
logger = logging.getLogger("aiserver.custom")

class Custom(Game):
    """This 'game mode' doesn't actually have server logic to verify your moves.
Everything you send will be sent directly to your opponent*. It's your job to honor the honor code and verify moves.

This is a turn-based system.

    * Technically not everything is sent. Everything you send that has a prefix of R will be sent to the opponent.
    Example: R something to send to opponent - something to send to opponent\n will be sent to the opponent.
"""

    name = "custom"
    def __init__(self, server, *players):
        Game.__init__(self, server, *players)
        self.commands = {
            "M" : self.send,
            "MSG" : self.send
        }

    def send(self, handler, *args):
        r"""Sends a message to the 'opponent'.
    Syntax: M <Your message>
    Example: M Hello World - Sends 'Hello World\n' to the opponent. (\n for line break)"""
        args = list(args)
        args.pop(0)
        self.opponent(handler, False).send(" ".join(args))

    def start(self):
        for player in self.players:
            player.send("PAIRED %s" % self.opponent(player))

    def shortDescription(self):
        return "Message passing service."
