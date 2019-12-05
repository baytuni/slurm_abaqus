#!/usr/bin/env python3
import os
import common
import socket

HOST = socket.gethostname()
PORT = 65432

if __name__ == "__main__":
    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(b'REMOVE 435 6 1 2019-11-19T09:12:51')
    response = s.recv(1024)
    if response.decode() == 'SUCCESS':
        print('ACCEPTED')
    else:
        print('REJECTED')

