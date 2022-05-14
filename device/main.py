from wifi_manager import WifiManager
from app.ota_updater import OTAUpdater
import time
import machine
import network
import gc
import ntptime

wm = WifiManager()
wm.connect()
time.pause(1)
ntptime.host = "us.pool.ntp.org"
if wm.is_connected():
    ntptime.host = "us.pool.ntp.org"    
    try:
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))
    except:
        print("Error syncing time")
Accept: application/vnd.github.v3+json
print('Memory free', gc.mem_free())
# token='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'
# otaUpdater = OTAUpdater('https://github.com/nalkema1/ESP32-Birdhouse', main_dir='app', headers={'Authorization': 'token {}'.format(token)})
otaUpdater = OTAUpdater('https://github.com/nalkema1/ESP32-Birdhouse', main_dir='app', headers={'Accept': 'application/vnd.github.v3+json'})

hasUpdated = otaUpdater.install_update_if_available()
if hasUpdated:
    machine.reset()
else:
    del(otaUpdater)
    gc.collect()