import time
from app.timesync import ntpsync
from app.timesync import myTime
from app.wifi_manager import WifiManager
import machine
from machine import Pin
from time import sleep
import urequests
import ujson
import camera
import binascii
import os
import esp32
import gc

prod = False # run without network
buf = None
path = '/photos'
motion = False
reboot = False
start_time = time.ticks_ms()
power_on = time.ticks_ms()


def setCPU(size):
    if size == 3:
        print("CPU set to 16 mhz")
        machine.freq(160000000)
        return
    if size == 2:
        print("CPU set to 8 mhz")
        machine.freq(80000000)
        return
    else:
        print("CPU set to 4 mhz")
        machine.freq(40000000)

def UploadAllPhotos():
    import os

    path = "/photos"
    for f in os.listdir("/photos"):
            filename = "{}/{}".format(path, f)
            print("Saving to cloud: ", filename)
            with open(filename,'r') as fp:
                data = fp.read()
            SavePhotoToAzure(data, filename[0:-4])

    machine.reset()

def TakePicture(flash=False):
    if flash:
        led = machine.Pin(4, machine.Pin.OUT)
        led.on()
        camera.init(0)
        led.on()
        buf = camera.capture()
        led.off()
        camera.deinit()
        return buf
    else:
        camera.init(0)
        buf = camera.capture()
        camera.deinit()
        return buf

def SavePhotoToDisk(photodata):
    filename = ""
    dict = {}

    dict["motion_gmtime"] = time.gmtime()

    for i in dict["motion_gmtime"]:
        filename = filename + str(i)
    
    filename = 'photos/'+filename+'.jpg'
    print("Saving: ", filename)

    with open(filename, 'w') as datafile:
        datafile.write(binascii.b2a_base64(photodata))
    datafile.close()

def ConnectToNetwork():

    global wm

    if not wm.is_connected():
        for retries in range(5):
            wm.connect(prod)
            if wm.is_connected():
                break
            else:
                time.sleep(1)
        ntpsync()

def SavePhotoToAzure(photodata, gmtime):
    dict = {}

    ConnectToNetwork()
    if wm.is_connected():
        dict["motion_gmtime"] = gmtime
        dict["photo"] = binascii.b2a_base64(photodata)
        encoded = ujson.dumps(dict)
        response = urequests.post("https://birdhouse.azurewebsites.net/api/birdhouse", headers = {'content-type': 'application/json'}, data = encoded)
        start_time = time.ticks_ms()
        print("Photo saved to Azure service ", response.text)
    else:
        print("Unable to save, network unavailable")


def CheckSchedule(timer):
    
    if prod:
        led = machine.Pin(15, machine.Pin.OUT)
        theTime = myTime()
        if theTime[3] > 20 and theTime[3] < 23:
            led.on()
        else:
            led.off()
    
    time_now = time.ticks_ms()
    if time.ticks_diff(time_now, power_on) > 3.6e+6:
        machine.reset()
        
    time_past = time.ticks_diff(time_now, start_time)
    print("time since last movement ", time_now, start_time, time_past)
    if time_past> 60000:
        # goto deepsleep if there has been not activity in 60 seconds
        print("Going to sleep.. ")
        machine.lightsleep()
        TurnLightsOn()

def TurnLightsOn():
    
    light = machine.Pin(15, machine.Pin.OUT)
    light.on()

def TurnLightsOff():
    
    light = machine.Pin(15, machine.Pin.OUT)
    light.off()

def handle_interrupt(pin):
    global motion
    global cycle
    global start_time
    global timer
    global wake
    global buf
    motion = True

    #reset the sleep timer
    start_time = time.ticks_ms()
 
    buf = TakePicture(True)
    
    if len(buf) > 0:
        print("Photo successful")
        if gc.mem_free() > 500000:
            # stop saving picture as we are running low on space
            SavePhotoToDisk(buf)
 
   # setCPU(2)


data = {}

wm = WifiManager()
ConnectToNetwork()

if wm.is_connected():
    currentTime = myTimeAsDict()
    try:
        with open('last_update.txt','r') as f:
            data = ujson.loads(f.read())
    except:
        data["day"] = 99

    if data["day"] != currentTime["day"]:
        print("Checking for software update....")
        otaUpdater = OTAUpdater('https://github.com/nalkema1/ESP32-Birdhouse', main_dir='app', headers={'Accept': 'application/vnd.github.v3+json'})

        hasUpdated = otaUpdater.install_update_if_available()
        if hasUpdated:
            machine.reset()
        else:
            del(otaUpdater)
            gc.collect()

        with open('last_update.txt','w') as f:
            ujson.dump(currentTime, f)

    if wm.is_connected():
        for i in range(10):
            TurnLightsOn()
            time.sleep(.2)
            TurnLightsOff()
            time.sleep(.2)
    else:
        for i in range(10):
            TurnLightsOn()
            time.sleep(1)
            TurnLightsOff()
            time.sleep(.2)

pir = Pin(13, Pin.IN)
pir.irq(trigger=Pin.IRQ_RISING, handler=handle_interrupt)
wake1 = Pin(13, mode = Pin.IN)
esp32.wake_on_ext0(pin = wake1, level = esp32.WAKEUP_ANY_HIGH)

timer = machine.Timer(0)  
timer.init(period=20000, mode=machine.Timer.PERIODIC, callback=CheckSchedule)

try:
    os.mkdir(path)
except:
    pass

# check camera
try:
    camera.framesize(12) # between 0 and 13
    camera.quality(63) # between 9 and 64
    camera.contrast(0) # between -3 and 3
    camera.saturation(0) # between -3 and 3
    camera.brightness(0) # between -3 and 3
    camera.speffect(3) # between 0 and  7
    camera.whitebalance(2) # between 0 and 5
    camera.framesize(camera.FRAME_QHD)
    camera.init(0, format=camera.JPEG)

    buf = camera.capture()
    camera.deinit()
except:
    machine.reset()

# for demo-mode, just turn the lights on:
TurnLightsOn()

# setCPU(2)

while True:

    if motion:
        print(gc.mem_free())
        if gc.mem_free() < 1500000 and wm.is_connected():
            UploadAllPhotos()

        print("Motion detected - in main loop")
        motion = False


