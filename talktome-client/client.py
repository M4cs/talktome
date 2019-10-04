import socket
import select
import errno
from argparse import ArgumentParser
import PySimpleGUIQt as g
import sys
import os
import threading
HEADER_LENGTH = 10
class GUI:
    def __init__(self, username, ip=None, port=3376, url=None):
        self.running = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = username
        self.url = url
        self.ip = ip
        self.port = port
        self.window = None
        self.chat_history = []

    def background(self):
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
                    self.chat_history.append('{:<2} {:<2} {:<}'.format(user, '|', message))
                    self.window.FindElement('history').Update('\n'.join(self.chat_history[-3:]))

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
    
    def show_window(self):
        b = threading.Thread(name='poller', target=self.background)
        b.daemon = True
        b.start()
        layout = [
            [g.T('TalkToMe: Connected')],
            [g.Output(size=(127, 30), key='history')],
            [g.Multiline(size=(85, 5), enter_submits=True, key='input', do_not_clear=False)],
            [g.B('Exit'), g.B('Send', bind_return_key=True)]
        ]
        self.window = g.Window('TalkToMe Client', grab_anywhere=True, keep_on_top=True, layout=layout)
        history_offset = 0
        while True:
            event, values = self.window.Read()
            print(event)
            if 'Send' in event:
                print('sending')
                msg = values['input'].strip()
                try:
                    message = msg.encode('utf-8')
                    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
                    self.client_socket.send(message_header + message)
                except:
                    raise Exception('Unexpected Error!')
                self.chat_history.append('{:<2} {:<1} {:<} '.format(str(self.username), '|', msg))
                history_offset = len(self.chat_history)-1
                self.window.FindElement('input').Update('')
                self.window.FindElement('history').Update('\n'.join(self.chat_history[-3:]))
            elif 'Up' in event and len(self.chat_history):
                command = self.chat_history[history_offset]
                history_offset -= 1 * (history_offset > 0)      # decrement is not zero
                self.window.FindElement('input').Update(command)
            elif 'Down' in event and len(self.chat_history):
                history_offset += 1 * (history_offset < len(self.chat_history)-1) # increment up to end of list
                command = self.chat_history[history_offset]
                self.window.FindElement('input').Update(command)
            elif 'Escape' in event:
                self.window.FindElement('query').Update('')
            elif 'Exit' in event:
                self.window.Close()
                break
        exit()
            
    
    def start(self):
        if self.url:
            if ':' in self.url:
                url_split = self.url.split(':')
                print(url_split)
                port = url_split[1]
                if len(port) >= 6:
                    raise Exception('Error! Port Number Must Have A Length Of 5 or Less!')
                else:
                    self.port = port
                    try:
                        self.ip = socket.gethostbyname_ex(url_split[0])[2][0]
                    except:
                        raise Exception('Error! Couldnt Get The IP From That URL!')
        else:
            if self.ip == None:
                raise Exception('Error! No IP Specified.')
        print(self.ip)
        self.client_socket.connect((self.ip, int(self.port)))
        self.client_socket.setblocking(False)
        self.running = True
        user = username.encode('utf-8')
        user_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(user_header + user)
        self.show_window()
        exit()
        
def start_screen():
    layout = [
        [g.T('TalkToMe Client')],
        [g.T('Username:', justification='center')],
        [g.I('', justification='center', key='username', focus=True)],
        [g.T('Enter URL:', justification='center')],
        [g.I('', justification='center', key='url')],
        [g.T('OR')],
        [g.T('Enter IP:'), g.I('', key='ip'), g.T('Enter Port:'), g.I('', key='port')],
        [g.B('Cancel'), g.B('Connect')]
    ]
    
    window = g.Window('TalkToMe', keep_on_top=True, grab_anywhere=True, layout=layout)
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
                    ], keep_on_top=True, grab_anywhere=True).Read()
                else:
                    window.Close()
                    return values['ip'], values['port'], values['url'], values['username']
            else:
                if values['ip'] != '':
                    if values['username'] == '':
                        g.Window('Error', auto_close=True, auto_close_duration=2, layout=[
                            [g.T('Error! Missing Username!')]
                        ], keep_on_top=True, grab_anywhere=True).Read()
                    if values['port'] != '':
                        window.Close()
                        return values['ip'], values['port'], values['url'], values['username']
                    else:
                        g.Window('Error', auto_close=True, auto_close_duration=2, layout=[
                        [g.T('Error! Missing Port!')]
                    ], keep_on_top=True, grab_anywhere=True).Read()
                else:
                    g.Window('Error', auto_close=True, auto_close_duration=2, layout=[
                        [g.T('Error! Missing IP!')]
                    ], keep_on_top=True, grab_anywhere=True).Read()

ip, port, url, username = start_screen()
if url:
    gui = GUI(username, url=url)
    gui.start()
    exit()
else:
    gui = GUI(username, ip=ip, port=port)
    gui.start()
    exit()

start_screen()