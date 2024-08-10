from datetime import datetime

# Current Date & Time as DateTime object
DTTM = datetime.now()

# # Current Date
DT = DTTM.date()

# Current Time
TM = DTTM.time()

#Current Date & Time as STR
TODAY,junk=(str(DTTM)).split(".")

