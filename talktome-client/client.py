import socket
import select
import errno
from argparse import ArgumentParser
import PySimpleGUIQt as g
import sys
import os
import threading
HEADER_LENGTH = 10
class BackgroundThread(threading.Thread, GUI):
    def run(self):
        while True:
            try:
                # Now we want to loop over received messages (there might be more than one) and print them
                while True:

                    # Receive our "header" containing username length, it's size is defined and constant
                    user_header = self.client_socket.recv(HEADER_LENGTH)

                    # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                    if not len(user_header):
                        print('Connection closed by the server')
                        sys.exit()

                    # Convert header to int value
                    username_length = int(user_header.decode('utf-8').strip())

                    # Receive and decode username
                    user = self.client_socket.recv(username_length).decode('utf-8')

                    # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                    message_header = self.client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')

                    # Print message
                    print('\n{:<2} {:<2} {:<}'.format(user, '|', message))

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
                
class GUI:
    def __init__(self, username, client_socket, ip=None, port=3376, url=None):
        self.running = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = username
        self.url = url
        self.ip = ip
        self.port = port
    
    def start(self):
        if self.url:
            if ':' in self.url:
                url_split = self.url.split(':')
                port = url_split[1]
                if len(port) >= 6:
                    raise Exception('Error! Port Number Must Have A Length Of 5 or Less!')
                else:
                    self.port = port
                    try:
                        self.ip = socket.gethostbyname(url_split[0])
                    except:
                        raise Exception('Error! Couldnt Get The IP From That URL!')
        else:
            if self.ip == None:
                raise Exception('Error! No IP Specified.')
        self.client_socket.connect((self.ip, self.port))
        self.client_socket.setblocking(False)
        self.running = True
        user = username.encode('utf-8')
        user_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(user_header + user)
        
def start_screen():
    layout = [
        [g.T('TalkToMe Client')],
        [g.T('Username:', justification='center')],
        [g.I('', justification='center', key='username', focus=True)],
        [g.T('Enter URL:', justification='center')],
        [g.I('0.tcp.ngrok.io:15564', justification='center', key='url')],
        [g.T('OR')],
        [g.T('Enter IP:'), g.I('192.168.1.68', key='ip'), g.T('Enter Port:'), g.I('3376', key='port')],
        [g.B('Cancel'), g.B('Connect')]
    ]
    
    window = g.Window('TalkToMe', keep_on_top=True, grab_anywhere=True, no_titlebar=True, layout=layout)
    while True:
        event, values = window.Read()
        print(event)
        print(values)
        if event == 'Cancel':
            exit()
        elif event == 'Connect':
            if values['url']:
                if values['username'] == '':
                    g.Window('Error', auto_close=True, auto_close_duration=2, layout=[
                        [g.T('Error! Missing Username!')]
                    ], keep_on_top=True, grab_anywhere=True, no_titlebar=True).Read()
            

# parser = ArgumentParser()
# parser.add_argument('-ip', '--ip', help='IP Address For Chat Server')
# parser.add_argument('-p', '--port', help='Port Number To Run Server On (Defaults To 3376)', type=int)

# def clear_screen():
#     if 'win' in sys.platform:
#         return os.system('cls')
#     else:
#         return os.system('clear')

# 
    
# args = parser.parse_args()
# if type(args.ip) == str:
#     hostname = socket.gethostbyname_ex(args.ip)[2][0]
# else:
#     hostname = args.ip
# IP = hostname
# PORT = args.port if args.port else 3376
# try:
#     columns, rows = os.get_terminal_size(0)
# except OSError:
#     columns, rows = os.get_terminal_size(1)
# startup = True
# while startup:
#     clear_screen()
#     print('Welcome To The TalkToMe Client!'.center(columns))
#     print('Please Enter A Username:'.center(columns))
#     username = input('\r\n'.center(columns - 5))
#     while True:
#         clear_screen()
#         print('Confirm Your Username: {}'.format(username).center(columns))
#         print('[Y\\N]:'.center(columns))
#         conf = input('\r\n'.center(columns)).lower()
#         if conf == 'y':
#             startup = False
#             break
#         elif conf == 'n':
#             break
#         else:
#             continue
# clear_screen()
# print('Joining Server Room...'.center(columns))
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect((IP, PORT))
# client_socket.setblocking(False)

# user = username.encode('utf-8')
# user_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
# client_socket.send(user_header + user)
            
# b = BackgroundThread()
# b.daemon = True
# b.start()
# def foreground():
#     while True:
#         message = input('{:<2} {:<1} {:<} '.format(str(username), '|', '>'))
#         if message:
#             # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
#             if message == "exit":
#                 clear_screen()
#                 print('Exiting...'.center(columns))
#                 exit()
#             message = message.encode('utf-8')
#             message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
#             client_socket.send(message_header + message)
# f = threading.Thread(name='chat', target=foreground)
# f.start()
# exit()

start_screen()