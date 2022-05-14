from app.wifi_manager import WifiManager
from app.ota_updater import OTAUpdater
import time
import machine
import network
import gc
import ntptime

time.sleep(3)
print("Starting Network")
wm = WifiManager()
for retries in range(5):
    wm.connect()
    if wm.is_connected():
        break
    else:
        time.sleep(2)

ntptime.host = "us.pool.ntp.org"
if wm.is_connected():
    ntptime.host = "us.pool.ntp.org"
    ntpsync = False
    for retries in range(3):    
        try:
            ntptime.settime()
            ntpsync = True
            break
        except:
            print("Error syncing time, retrying...")
    if ntpsync:
        print("Local time after synchronization：%s" %str(time.localtime()))
    else:
        print("Error syncing time") 

print('Memory free', gc.mem_free())

otaUpdater = OTAUpdater('https://github.com/nalkema1/ESP32-Birdhouse', main_dir='app', headers={'Accept': 'application/vnd.github.v3+json'})

hasUpdated = otaUpdater.install_update_if_available()
if hasUpdated:
    machine.reset()
else:
    del(otaUpdater)
    gc.collect()