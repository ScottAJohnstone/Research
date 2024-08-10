
# Research V2:	RUNNER 
# Command line program for managing and logging land research related files and documents.

# Standard Imports
import os
import tkinter as tk
# Relative Imports
from UTILITY import date_time as dt
from UTILITY import math as m


# Definitions
def prelim():
    #TODAY,junk=(str(dt.dttm)).split(".")
    TODAY=dt.TODAY
    CDATE = (f'hello')  
    print(CDATE)

def fullpath(path):
    #Returns the full path of a file or directory.
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path)))

def start():
    start = tk.Tk()
    start.mainloop()

#Calls
prelim()