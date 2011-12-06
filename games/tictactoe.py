from games import Game
import random
import logging
import collections

class TicTacToe(Game):
    """Tic Tac Toe game. Game syntax after you are paired with an opponent is as follows:
    1. START <opponent> <0/1> [YOURTURN]
        This message is the first message sent to you by the server after being paired.
        <opponent> is the name of the opponent.
        <0/1> is either 0 or 1 and it signals what your piece will be denoted as.
        [YOURTURN] is optional. If it is present, it signals it's your move.
    2. PLACE <row> <col>
        This message is sent by you. It places a piece in the tic tac toe board.
        <row> - 0 to 2. From 0th row to 2nd row
        <col> - 0 to 2. From 0th column to the 2nd column
    3. x x x,x x x,x x x
        This is the board state sent back to you after the opponent makes a move.
        x can be anything from -1 to 1, where -1 is empty and 0/1 are either yours or enemy's. See the START message for your piece.
    4. WON <name>
        This is sent to you after someone wins a game.
        <name> is the name of the player that won.
    5. TIE
        This is sent to you after the game has been tied.
    """

    @staticmethod
    def shortDescription():
        return "Simple tic tac toe game. Proof of concept."

    name = "tictactoe"

    def __init__(self, server, *players):
        Game.__init__(self, server, *players)
        self.commands = {
            "PLACE" : self.place,
            "STATUS" : self.status
        }

    def status(self, handler, *args):
        """Checks the status of the board. If it's not your turn, it will send back 'OPPONENT_THINKING'
    Note: if opponent has been disconnected, you will get 'CONNECTION_BROKEN'"""
        pnum = self.players.index(handler)
        if pnum != self.currentTurn:
            handler.send("OPPONENT_THINKING")
        else:
            handler.send(self.strboard())

    def start(self):
        self.board = ([-1, -1, -1], [-1, -1, -1], [-1, -1, -1])
        self.currentTurn = random.choice((0, 1))
        for i, player in enumerate(self.players):
            message = "START " + self.players[int(not i)].username + " " + str(i)
            if i == self.currentTurn:
                message += " YOURTURN"
            player.send(message)

    def flipTurn(self):
        self.currentTurn = int(not self.currentTurn)

    def endMsg(self, i):
        if i == 2:
            return "TIE " + self.strboard()
        else:
            return "WON " + self.players[i].username + " " + self.strboard()

    def place(self, handler, *args):
        try:
            row = int(args[1])
            col = int(args[2])
        except:
            handler.sendStatus(400, "Malformed data")
            import traceback
            logging.warning(traceback.format_exc())
            return

        playerNum = self.players.index(handler)
        if playerNum != self.currentTurn:
            handler.sendStatus(403, "Not your turn")
        else:
            if row not in (0, 1, 2) or col not in (0, 1, 2) or self.board[row][col] != -1:
                handler.sendStatus(403, "Invalid Location")
            else:
                self.board[row][col] = playerNum
                victory = self.checkVictory()
                if victory > -1:
                    for player in self.players:
                        player.send(self.endMsg(victory))
                    self.server.endGame("tictactoe", self)
                else:
                    self.flipTurn()
                    self.players[self.currentTurn].send(self.strboard())

    def strboard(self):
        return ",".join(map(lambda row: " ".join(map(lambda col: str(col), row)), self.board))

    def checkVictory(self):
        board = self.board
        draw = True
        for i in xrange(3):
            r = self.rowcount(i)
            c = self.colcount(i)
            if i < 3:
                d = self.diagcount(i)
            else:
                d = {-1: 0, 0: 0, 1: 0}

            for j in xrange(0, 2):
                if d[j] == 3 or r[j] == 3 or c[j] == 3:
                    return j
            if r[-1] > 0 or c[-1] > 0:
                draw = False

        if draw:
            return 2
        return -1

    def rowcount(self, row):
        return collections.Counter(self.board[row])

    def colcount(self, col):
        return collections.Counter([self.board[i][col] for i in xrange(3)])

    def diagcount(self, left=True):
        if left:
            a = [self.board[0][0], self.board[1][1], self.board[2][2]]
        else:
            a = [self.board[0][2], self.board[1][1], self.board[2][0]]

        return collections.Counter(a)


