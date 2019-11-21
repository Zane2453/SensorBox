from iottalkpy import dan
from config import IoTtalk_URL, device_model, device_name, Comm_interval, idf_list
import sys
import time
import requests
import os
import datetime
import json

sys.path.insert(0, '/usr/lib/python2.7/bridge/')
from bridgeclient import BridgeClient

client = BridgeClient()

def LED_flash(LED_state):
    if LED_state:
        client.put('Reg_done', '1')
        os.system(r'echo "timer" > /sys/class/leds/ds:green:usb/trigger')      #For ArduinoYun Only. LED Blink.
    else:
        client.put('Reg_done', '0')
        os.system(r'echo "none" > /sys/class/leds/ds:green:usb/trigger')

''' IoTtalk data handler '''
def on_data(odf_name, data):
    print("[da] [data] ", odf_name, data)

def on_signal(signal, df_list):
    print('[cmd]', signal, df_list)

def on_register():
    dan.log.info('[da] register successfully')

''' IoTtalk registration '''
def device_registration_with_retry():
    #device_addr = "{:012X}".format(getnode())
    context = dan.register(
        IoTtalk_URL,
        on_signal=on_signal,
        on_data=on_data,
        idf_list=idf_list,
        accept_protos=['mqtt'],
        name=device_name,
        #id_=device_addr,
        profile={
            'model': device_model
        },
        on_register=on_register
    )

device_registration_with_retry()
LED_flash(1)

if __name__ == "__main__":
    isChange = 0
    resetCounter = 1
    reConnecting = 0

    while True:
        try:
            for f_name, type_ in idf_list:
                type_ = json.dump(type_)
                tmp = client.get(f_name)
                if tmp is None:
                    continue
                else:
                    client.delete(f_name)

                v = type_(tmp)
                if v is not None:
                    os.system(r'echo "default-on" > /sys/class/leds/ds:green:wlan/trigger')
                    print('DAN.push({f}, {v!r})'.format(f=f_name, v=v, ))
                    dan.push(f_name, v)
                    os.system(r'echo "none" > /sys/class/leds/ds:green:wlan/trigger')

            if reConnecting:
                LED_flash(1)
                reConnecting = 0

        except Exception as e:
            print(e)
            LED_flash(0)

            if str(e).find('mac_addr not found:') != -1:
                print('Reg_addr is not found. Try to re-register...')
                reConnection = 1
                device_registration_with_retry()
            else:
                print('Connection failed due to unknow reasons.')
                reConnecting = 1
                time.sleep(1)

        if datetime.datetime.now().hour == 0 and not isChange:  # reset counter to zero at 00 o'clock
            client.put('resetCounter', str(resetCounter))
            isChange = 1
            resetCounter = resetCounter + 1 % 1000
        print('Reset Bug and RainMeter counter.')

        if datetime.datetime.now().hour == 12:
            isChange = 0

        time.sleep(Comm_interval)