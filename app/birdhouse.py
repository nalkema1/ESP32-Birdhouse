import time
import machine
from machine import Pin
from time import sleep
import urequests
import ujson
import camera
import binascii
import os
import esp32


path = '/photos'
motion = False
reboot = False
start_time = time.ticks_ms()
power_on = time.ticks_ms()
dict = {}

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

def myTime():
    UTC_OFFSET = -4 * 60 * 60   # change the '-4' according to your timezone
    return time.localtime(time.time() + UTC_OFFSET)

def CheckSchedule(timer):
    
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
    if time_past> 10000:
        # goto deepsleep if there has been not activity in 10 seconds
        print("Going to sleep.. ")
        machine.lightsleep()

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
    motion = True

    machine.disable_irq()
    timer.deint()
 
    #reset the sleep timer
    start_time = time.ticks_ms()
    camera.framesize(12) # between 0 and 13
    camera.quality(63) # between 9 and 64
    camera.contrast(0) # between -3 and 3
    camera.saturation(0) # between -3 and 3
    camera.brightness(0) # between -3 and 3
    camera.speffect(3) # between 0 and  7
    camera.whitebalance(2) # between 0 and 5
    camera.framesize(camera.FRAME_QHD)

    # camera.agcgain(0) # between 0 and 30
    # camera.aelavels(0) # between -3 and 3
    # camera.aecvalue(100) # between 0 and 1200
    # camera.pixformat(0) # 0 for JPEG, 1 for YUV422 and 2 for RGB

    # take Photo
    try:
        camera.init(0, format=camera.JPEG)
    except:
        camera.deinit()
        machine.reset()   
        return

    setCPU(3)
    led = machine.Pin(4, machine.Pin.OUT)
    led.on()
    buf = camera.capture()
    camera.deinit()    
    led.off()
    
    if len(buf) > 0:
        print("Photo successful")
        filename = ""
        dict["motion_gmtime"] = time.gmtime()
        # for i in dict["motion_gmtime"]:
        #     filename = filename + str(i)
        # filename = 'photos/'+filename+'.jpg'
        # print(filename)
        # with open(filename, 'w') as datafile:
        #     datafile.write(binascii.b2a_base64(buf))
        # datafile.close()

        from app.wifi_manager import WifiManager

        wm = WifiManager()
        if not wm.is_connected():
            for retries in range(5):
                wm.connect()
                if wm.is_connected():
                    break
                else:
                    time.sleep(1)

        dict["photo"] = binascii.b2a_base64(buf)
        encoded = ujson.dumps(dict)
        response = urequests.post("https://birdhouse.azurewebsites.net/api/birdhouse", headers = {'content-type': 'application/json'}, data = encoded)
        start_time = time.ticks_ms()
        print("Photo saved to Azure service ", response.text)
    else:
        print("Photo failed")

    wake1 = Pin(13, mode = Pin.IN)
    esp32.wake_on_ext0(pin = wake1, level = esp32.WAKEUP_ANY_HIGH)

    timer = machine.Timer(0)  
    timer.init(period=20000, mode=machine.Timer.PERIODIC, callback=CheckSchedule)

    setCPU(2)


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

# signal that device is ready

for i in range(4):
    TurnLightsOn()
    time.sleep(.3)
    TurnLightsOff()
    time.sleep(.3)

setCPU(2)
while True:

    if motion:
        print("Motion detected - in main loop")
        motion = False


