import json
import random
import time
import requests
import datetime
import os
import pytz
from datetime import timedelta
from google.cloud import pubsub
from google.cloud import datastore

dsclient=datastore.Client()

def fetchWeatherData(sensor):
    latitude=sensor['Location'].latitude
    longitude=sensor['Location'].longitude
    url='https://api.openweathermap.org/data/2.5/weather?lat='+str(latitude)+'&lon='+str(longitude)+'&units=imperial&appid=866eef7caa9458456e9b0bc80f294a7f'
    response=requests.post(url)
    weather={}
    weather['sensorID']=sensor.id
    weather['predict']=False
    weather['timecollected']=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    weather['temperature']=response.json()['main']['temp']
    weather['pressure']=response.json()['main']['pressure']
    weather['humidity']=response.json()['main']['humidity']
    weather['dewpoint']=(weather['temperature'] - float(9)/25*(100-weather['humidity']))
    #https://en.wikipedia.org/wiki/Dew_point
    return weather

def fetchSensorInfo():
    start_date = datetime.datetime.now() - timedelta(minutes = 30)
    query = dsclient.query(kind='Locations')
    query.add_filter('LastSeen', '<', start_date)
    location = list(query.fetch(1))
    if len(location) > 0:
        return location[0]
    else:
        return False

def updateSensorLastSeen(sensor):
    with dsclient.transaction():
        sensor['LastSeen']=datetime.datetime.now(tz=pytz.utc)# - timedelta(minutes=45)
        print sensor['LastSeen'] 
        dsclient.put(sensor)

def publishWeather(sensor, weatherData):
    latitude=sensor['Location'].latitude
    longitude=sensor['Location'].longitude
    publisher = pubsub.PublisherClient()
    topic = 'projects/ml-demo-212200/topics/iot-topic'.format(
        project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
        topic='MY_TOPIC_NAME',  # Set this to something appropriate.
    )
    publisher.publish(topic, json.dumps(weatherData), projectId='ml-demo-212200', deviceRegistryId='iot-registry', deviceNumId='000000000000000', deviceId='esp32_virtual', deviceRegistryLocation='us-central1')

time.sleep(random.randrange(0,30))

timeout = time.time() + 60*5
sensor = fetchSensorInfo()
while not sensor:
    print 'trying sensor'
    sensor = fetchSensorInfo()
    if time.time() > timeout:
        break
    time.sleep(5)

if sensor:
    while True:
        updateSensorLastSeen(sensor)
        weatherData=fetchWeatherData(sensor)
        publishWeather(sensor, weatherData)
        time.sleep(60)
