from wifi_manager import WifiManager
import time
import ntptime

wm = WifiManager()
wm.connect()

# while True:
#     if wm.is_connected():
#         print('Connected!')
#     else:
#         print('Disconnected!')
#     utime.sleep(10)

ntptime.host = "us.pool.ntp.org"
if wm.is_connected():
    ntptime.host = "us.pool.ntp.org"    
    try:
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))
    except:
        print("Error syncing time")