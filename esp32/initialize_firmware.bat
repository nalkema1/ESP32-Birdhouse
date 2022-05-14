rem managed by https://github.com/shariltumin/esp32-cam-micropython
esptool.py --port com9 --baud 460800 write_flash -z 0x1000 firmware.bin
