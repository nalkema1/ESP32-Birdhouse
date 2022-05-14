import urandom
import math
import time
from machine import Pin
from time import sleep
import urequests
import ujson
import camera

dict = {}

def TakePicture():

    camera.framesize(12) # between 0 and 13
    camera.quality(63) # between 9 and 64
    camera.contrast(0) # between -3 and 3
    camera.saturation(0) # between -3 and 3
    camera.brightness(0) # between -3 and 3
    camera.speffect(3) # between 0 and  7
    camera.whitebalance(2) # between 0 and 5
    camera.framesize(camera.FRAME_QHD)
    
    try:
        camera.init(0, format=camera.JPEG)
    except:
        pass

    led = machine.Pin(4, machine.Pin.OUT)
    led.on()
    buf = camera.capture()
    led.off()
    if len(buf) > 0:
        camera.deinit()
        return buf
        print("Photo successful")
    else:
        camera.deinit()
        return None

motion = False

def handle_interrupt(pin):
    global motion
    global cycle

    motion = True
    dict["motion_gmtime"] = time.gmtime()
    photo = TakePicture()
    if photo:
        dict["photo"] = photo
    encoded = ujson.dumps(dict)
    response = urequests.post("https://birdhouse.azurewebsites.net/api/birdhouse", headers = {'content-type': 'application/json'}, data = encoded)
    print(response.text)

    global interrupt_pin
    interrupt_pin = pin 

pir = Pin(13, Pin.IN)
pir.irq(trigger=Pin.IRQ_RISING, handler=handle_interrupt)

while True:

    if motion:
        print("Motion detected")
        motion = False
    pass

