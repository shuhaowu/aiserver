#!/usr/bin/python
import gtk
import gtk.glade
import gobject
import socket

class TicTacToeTestClient(object):
    def __init__(self):
        self.setInitial()
        self.socket = None

        self.builder = builder = gtk.Builder()
        builder.add_from_file("tictactoe-test.glade")
        builder.connect_signals(self)

        self.boardButtons = [[None, None, None], [None, None, None], [None, None, None]]
        for i in xrange(9):
            row = i / 3
            col = i % 3
            self.boardButtons[row][col] = cb = builder.get_object("block" + str(i))
            cb.connect("clicked", self.onBoardClick, (row, col))


        def f(event, callback):
            if gtk.gdk.keyval_name(event.keyval) == "Return":
                callback()

        self.entryIP = builder.get_object("entryIP")
        self.entryIP.set_text("serverip")
        self.entryIP.connect("key-release-event", lambda widget, event: f(event, self.on_btnConnect_clicked))
        self.entryUsername = builder.get_object("entryUsername")
        self.entryUsername.set_text("testacc i6AgKTH+'=vEh<jZ5#;t")
        self.entryUsername.connect("key-release-event", lambda widget, event: f(event, self.on_btnLogin_clicked))
        self.btnConnect = builder.get_object("btnConnect")
        self.btnDisconnect = builder.get_object("btnDisconnect")
        self.btnLogin = builder.get_object("btnLogin")
        self.btnReady = builder.get_object("btnReady")
        self.btnStatus = builder.get_object("btnStatus")

        self.lblStatus = builder.get_object("lblStatus")

        self.window = builder.get_object("mainWindow")
        self.window.show_all()
        gtk.main()

    def gtk_main_quit(self, *args):
        self.on_btnDisconnect_clicked()
        gtk.main_quit()

    def updateBoard(self, boardstr):
        board = boardstr.split(",")
        self.board = map(lambda row: map(lambda i: int(i), row.split()), board)
        self.refresh()

    def gameEnds(self):
        self.opponent = False
        self.myTurn = False
        self.myPiece = None
        self.readied = False
        self.refresh()

    def boardHandler(self, source, condition):
        data = source.recv(1024)
        data = data.strip()
        print "Enemy Moved: " + data
        if data == "CONNECTION_BROKEN":
            self.lblStatus.set_label("Your opponent has disconnected!")
            self.gameEnds()
        elif data.startswith("TIE"):
            self.updateBoard(data.split(" ", 1)[1])
            self.gameEnds()
            self.lblStatus.set_label("Game Tied!")
        elif data.startswith("WON"):
            data = data.split(" ", 2)
            self.updateBoard(data[2])
            self.gameEnds()
            if data[1] == self.username:
                self.lblStatus.set_label("You won!")
            else:
                self.lblStatus.set_label("You lost.")
        else:
            self.updateBoard(data)
            self.myTurn = True
        return False

    def onBoardClick(self, button, loc):
        if self.myTurn:
            if self.board[loc[0]][loc[1]] == -1:
                self.send("PLACE %d %d" % loc, self.boardHandler)
                self.board[loc[0]][loc[1]] = self.myPiece
                self.myTurn = False
                self.refresh()
            else:
                self.lblStatus.set_label("You're not allowed to place there!")
        else:
            self.lblStatus.set_label("It's not your turn!")

    def on_btnStatus_clicked(self, *args):
        self.socket.send("STATUS")
        data = self.socket.recv(1024).strip()

        if data == "OPPONENT_THINKING":
            self.lblStatus.set_label("Your opponent is still thinking.")
        elif data == "CONNECTION_BROKEN":
            self.gameEnds()
            self.lblStatus.set_label("Your opponent has disconnected!")
        elif data == "tictactoe":
            if not self.readied:
                self.lblStatus.set_label("You're not in a game. Press READY to start.")
        else:
            print "STATUS: " + data
            self.lblStatus.set_label("Nothing to report.")


    def on_btnConnect_clicked(self, *args):
        self.lblStatus.set_label("Connecting... GUI may freeze.")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(15)
        ip = self.entryIP.get_text().strip()
        try:
            self.socket.connect((ip, 6055))
        except socket.timeout, socket.error:
            self.lblStatus.set_label("Connection cannot be established.")
            self.socket = None
        else:
            data = self.socket.recv(1024)
            if data:
                self.connected = True
                print data

            self.refresh()

    def setInitial(self):
        self.connected = False
        self.opponent = False
        self.loggedIn = False
        self.readied = False
        self.myTurn = False
        self.myPiece = None
        self.username = None
        self.board = [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]]

    def refresh(self):
        self.btnConnect.set_sensitive(not self.connected)
        self.btnDisconnect.set_sensitive(self.connected)
        self.entryIP.set_sensitive(not self.connected)
        self.btnLogin.set_sensitive(not self.loggedIn)
        self.btnStatus.set_sensitive(self.loggedIn)
        self.entryUsername.set_sensitive(not self.loggedIn)
        self.btnReady.set_sensitive(self.loggedIn and not self.readied)

        if self.myTurn:
            self.lblStatus.set_label("It's your turn! Against: %s" % self.opponent)
        elif self.opponent:
            self.lblStatus.set_label("In game with %s" % self.opponent)
        elif self.readied:
            self.lblStatus.set_label("Waiting for an opponent...")
        elif self.loggedIn:
            self.lblStatus.set_label("Logged in to server!")
        elif self.connected:
            self.lblStatus.set_label("Connected into server. Please login.")
        else:
            self.lblStatus.set_label("Not connected.")

        for r, row in enumerate(self.boardButtons):
            for c, button in enumerate(row):
                button.set_sensitive(bool(self.opponent))
                if self.myPiece is not None:
                    l = self.board[r][c]
                    if l == -1:
                        l = ""
                    elif l == self.myPiece:
                        l = "X"
                    else:
                        l = "O"

                    button.set_label(l)

    def send(self, data, handler=None):
        if handler is None:
            def handler(source, condition):
                data = source.recv(1024)
                if len(data) > 0:
                    print "RECEIVED: " + data
                    return True
                else:
                    return False
        self.socket.send(data)
        gobject.io_add_watch(self.socket, gobject.IO_IN, handler)

    def on_btnDisconnect_clicked(self, *args):
        if self.socket:
            self.socket.send("QUIT")
            self.socket.close()
            self.socket = None
        self.setInitial()
        self.refresh()

    def on_btnLogin_clicked(self, *args):
        userpass = self.entryUsername.get_text().strip()
        def loginHandler(source, condition):
            data = source.recv(1024)
            data = data.split("\n")
            code = data[0].split(": ")
            code = code[1].strip()
            if code == "200":
                self.loggedIn = True
                self.username = userpass.split(" ")[0]
                self.socket.send("JOIN tictactoe")
                self.socket.recv(1024)
                self.refresh()
            else:
                self.socket.close()
                self.socket = None
                self.setInitial()
                self.refresh()
                self.lblStatus.set_label("Authorization failed.")

            return False
        self.send(userpass, loginHandler)

    def on_btnReady_clicked(self, button):
        def readyHandler(source, condition):
            data = source.recv(1024)
            data = data.strip().split(" ")
            if len(data) == 4:
                self.myTurn = True
            else:
                gobject.io_add_watch(self.socket, gobject.IO_IN, self.boardHandler)
            self.opponent = data[1]
            self.myPiece = int(data[2])
            print "My piece is %d" % self.myPiece
            self.board = [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]]
            self.refresh()
            return False

        self.send("READY", readyHandler)

        self.readied = True
        for row in self.boardButtons:
            for button in row:
                button.set_label("")
        self.refresh()


if __name__ == "__main__":
    TicTacToeTestClient()
