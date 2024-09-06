import os
import socket

def fullpath(path):
    #Returns the full path of a file or directory.
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))

def usr():
    computer_name = socket.gethostname()
usr()