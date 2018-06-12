import streams
import json
from wireless import wifi
from bosch.bme280 import bme280

# choose a wifi chip supporting secure sockets
from espressif.esp32net import esp32wifi as wifi_driver

import requests
# import google cloud iot module
from googlecloud.iot import iot

# import helpers functions to easily load keys and device configuration
import helpers

# DEVICE KEY FILE MUST BE PLACED INSIDE PROJECT FOLDER
new_resource('private.hex.key')
# set device configuration inside this json file
new_resource('device.conf.json')

# define a callback for config updates
def config_callback(config):
    global publish_period
    print('requested publish period:', config['publish_period'])
    publish_period = config['publish_period']
    return {'publish_period': publish_period}

streams.serial()
wifi_driver.auto_init()

# place here your wifi configuration
wifi.link("CASSINIguest",wifi.WIFI_WPA2,"Cassini2016!")

# BME280 Sensor
bmp = bme280.BME280(I2C1) # Connect SCL to IO17 and SDA to IO16
print("Starting BME280 Sensor...")
bmp.start()
print("Ready!")
print("--------------------------------------------------------")

pkey = helpers.load_key('private.hex.key')
device_conf = helpers.load_device_conf()
publish_period = 20000

# choose an appropriate way to get a valid timestamp (may be available through hardware RTC)
def get_timestamp():
    user_agent = {"user-agent": "curl/7.56.0"}
    return json.loads(requests.get('http://now.httpbin.org', headers=user_agent).content)['now']['epoch']
    

# create a google cloud device instance, connect to mqtt broker, set config callback and start mqtt reception loop
device = iot.Device(device_conf['project_id'], device_conf['cloud_region'], device_conf['registry_id'], device_conf['device_id'], pkey, get_timestamp)
device.mqtt.connect()
device.on_config(config_callback)
device.mqtt.loop()

while True:
    print('Publishing...')
    temp = bmp.get_temp()  # Read temperature
    hum  = bmp.get_hum()   # Read humidity
    prs  = bmp.get_press() # Read temperature
    print("Temperature: ", temp, "C, ", "Humidity: ", hum, "%rH, ", "Pressure: ", prs, "Pascal")
    #device.publish_event(json.dumps({ 'asample': random(0,10) }))
    device.publish_event(json.dumps({ 'temp': temp }, { 'hum': hum } ))
    sleep(publish_period)

