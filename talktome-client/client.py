import socket
import select
import errno
from argparse import ArgumentParser
import sys
import os
import threading
import curses
import curses.textpad
import datetime

TITLE = 'Max\'s Chat Room'

class Message:
    def __init__(self, time=None, name=None, text=None):
        self.time = time
        self.name = name
        self.text = text

class Layout:
    def __init__(self):
        try:
            self.columns, self.rows = os.get_terminal_size(0)
        except OSError:
            self.columns, self.rows = os.get_terminal_size(1)
        self.title_rows = 1
        self.title_cols = self.columns
        self.title_start_row = 0
        self.title_start_col = 0
        
        self.history_rows = self.rows - 2
        self.history_cols = self.columns
        self.history_start_row = 1
        self.history_start_col = 1
        
        self.prompt_rows = 1
        self.prompt_cols = self.columns
        self.prompt_start_row = self.rows - 1
        self.prompt_start_col = 0
        
class Title:
    def __init__(self, layout, screen):
        self.window = curses.newwin(layout.title_rows, layout.title_cols, layout.title_start_row, layout.title_start_col)
        start_col = (layout.title_cols - len(TITLE)) / 2
        self.window.addstr(int(0), int(start_col), TITLE, curses.A_BOLD)
        
    def redraw(self):
        self.window.refresh()
        
class History:
    def __init__(self, layout, screen):
        self.messages = []
        self.layout = layout
        self.screen = screen
        self.window = curses.newwin(layout.history_rows, layout.history_cols,
            layout.history_start_row, layout.history_start_col)
        # Because we have a border, the number of visible rows/cols is fewer
        self.visible_rows = self.layout.history_rows - 2
        self.visible_cols = self.layout.history_cols - 2

    def append(self, msg):
        "Append a Message object to the history. Does not redraw."
        self.messages.append(msg)

    def redraw(self):
        self.window.clear()
        self.window.border(0)

        # Draw the last N messages, where N is the number of visible rows
        row = 1
        for msg in self.messages[-self.visible_rows:]:
            self.window.move(row, 1)
            self.window.addstr(msg.name + ': ', curses.A_BOLD)
            self.window.addstr(msg.text)
            row += 1

        self.window.refresh()
        
class Prompt:
    def __init__(self, layout, screen):
        self.layout = layout
        self.screen = screen
        self.window = curses.newwin(layout.prompt_rows, layout.prompt_cols,
            layout.prompt_start_row, layout.prompt_start_col)
        self.window.keypad(1)
        self.window.addstr('> ')

    def getchar(self):
        "Get a single character from the user"
        return self.window.getch()

    def getstr(self):
        "Get an input string from the user"
        return self.window.getstr()

    def redraw(self):
        "Redraw the prompt window"
        self.window.refresh()

    def reset(self):
        "Reset the prompt to '> ' and redraw"
        self.window.clear()
        self.window.addstr('> ')
        self.redraw()

parser = ArgumentParser()
parser.add_argument('-ip', '--ip', help='IP Address For Chat Server')
parser.add_argument('-p', '--port', help='Port Number To Run Server On (Defaults To 3376)', type=int)

def clear_screen():
    if 'win' in sys.platform:
        return os.system('cls')
    else:
        return os.system('clear')

HEADER_LENGTH = 10
    
args = parser.parse_args()
if type(args.ip) == str:
    hostname = socket.gethostbyname_ex(args.ip)[2][0]
else:
    hostname = args.ip
try:
    columns, rows = os.get_terminal_size(0)
except OSError:
    columns, rows = os.get_terminal_size(1)
IP = hostname
PORT = args.port if args.port else 3376
startup = True
while startup:
    clear_screen()
    print('Welcome To The TalkToMe Client!'.center(columns))
    print('Please Enter A Username:'.center(columns))
    username = input('\r\n'.center(columns - 5))
    while True:
        clear_screen()
        print('Confirm Your Username: {}'.format(username).center(columns))
        print('[Y\\N]:'.center(columns))
        conf = input('\r\n'.center(columns)).lower()
        if conf == 'y':
            startup = False
            break
        elif conf == 'n':
            break
        else:
            continue
clear_screen()
print('Joining Server Room...'.center(columns))
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)

user = username.encode('utf-8')
user_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(user_header + user)

class BackgroundThread(threading.Thread):
    def run(self):
        while True:
            try:
                # Now we want to loop over received messages (there might be more than one) and print them
                while True:

                    # Receive our "header" containing username length, it's size is defined and constant
                    user_header = client_socket.recv(HEADER_LENGTH)

                    # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                    if not len(user_header):
                        print('Connection closed by the server')
                        sys.exit()

                    # Convert header to int value
                    username_length = int(user_header.decode('utf-8').strip())

                    # Receive and decode username
                    user = client_socket.recv(username_length).decode('utf-8')

                    # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                    message_header = client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = client_socket.recv(message_length).decode('utf-8')

                    # Print message
                    print('{:<2} {:<2} {:<} \r\n'.format(user, '|', message))

            except IOError as e:
                # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                # If we got different error code - something happened
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()

                # We just did not receive anything
                continue

            except Exception as e:
                # Any other exception - something happened, exit
                print('Reading error: {}'.format(str(e)))
                sys.exit()

class TalkToMe:
    running = False
    def __init__(self):
        self.layout = Layout()
        self.screen = None
    
    def _start_curses(self):
        if TalkToMe.running:
            raise Exception('Curses Is Running!')
        self.screen = curses.initscr()
        curses.cbreak()
        self.screen.keypad(1)
        TalkToMe.running = True
    
    def _stop_curses(self):
        if not TalkToMe.running:
            raise Exception("Curses is not running")
        curses.nocbreak()
        self.screen.keypad(0)
        self.screen = None
        curses.endwin()
        TalkToMe.running = False
        
    def redraw(self):
        self.screen.refresh()
        self.history.redraw()
        self.title.redraw()
        self.prompt.redraw()
        
    def start(self):
        debug = None
        input = ''
        try:
            self._start_curses()
            self.title = Title(self.layout, self.screen)
            self.history = History(self.layout, self.screen)
            self.prompt = Prompt(self.layout, self.screen)
            
            while True:
                self.redraw()
                text = self.prompt.getstr()
                if text == '':
                    continue
                if text == 'exit':
                    break
                now = datetime.datetime.now()
                msg = Message(now, username, text)
                message = text.encode('utf-8')
                message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                client_socket.send(message_header + message)
                self.history.append(msg)
                self.history.redraw()
                self.prompt.reset()
                
        except KeyboardInterrupt:
            pass

        # For other interrupts, re-raise them so we can debug
        except:
            if debug:
                msg = "Exception: " + str(sys.exc_info()[0]) + "\n"
                debug.write(msg)
            raise

        # Make sure to close the debug file
        finally:
            if debug:
                debug.close

    def stop(self):
        "Stop curses and stop the app. You must call this before exiting."
        self._stop_curses()


            
app = TalkToMe()
app.start()
