from time import sleep
from datetime import datetime
past = datetime.now()
sleep(100)
now = datetime.now()
diffa = (past - now).total_seconds()
diffb = (now - past).total_seconds()
print(diffa)
print(diffb)