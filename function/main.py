import base64
import json
import os
import sys
import time
import googleapiclient
from googleapiclient import discovery
from googleapiclient import errors
from google.cloud import bigquery
from google.cloud import pubsub
from google.cloud import pubsub
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import google.auth

def set_config( project_id, cloud_region, registry_id, device_id, score):
    api_version = 'v1'
    discovery_api = 'https://cloudiot.googleapis.com/$discovery/rest'
    service_name = 'cloudiotcore'

    scoped_credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    discovery_url = '{}?version={}'.format( discovery_api, api_version)

    client=discovery.build( service_name, api_version, discoveryServiceUrl=discovery_url, credentials=scoped_credentials)
    device_path = 'projects/{}/locations/{}/registries/{}/devices/{}'.format( project_id, cloud_region, registry_id, device_id)
    registry_name = 'projects/{}/locations/{}/registries/{}'.format( project_id, cloud_region, registry_id)
    device_name = '{}/devices/{}'.format(registry_name, device_id)
    devices = client.projects().locations().registries().devices()
    latest = devices.configVersions().list( name=device_name).execute().get( 'deviceConfigs', [])[0]['version']
    config={}
    config['score']=score
    config_body = { 'versionToUpdate': latest, 'binaryData': base64.urlsafe_b64encode(json.dumps(config).encode('utf-8')).decode('ascii') }

    return client.projects().locations().registries().devices().modifyCloudToDeviceConfig( name=device_path, body=config_body).execute()

def predict_json(project, model, instances, version=None):
    service = googleapiclient.discovery.build('ml', 'v1')
    name = 'projects/{}/models/{}'.format(project, model)

    if version is not None:
        name += '/versions/{}'.format(version)

    response = service.projects().predict(
        name=name,
        body={"instances": instances}
    ).execute()

    if 'error' in response:
        raise RuntimeError(response['error'])
    return response['predictions']

def pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    wd=json.loads(pubsub_message)
    print(wd)
    print(event)
    deviceId=event['attributes']['deviceId']
    deviceRegistryId=event['attributes']['deviceRegistryId']
    deviceRegistryLocation=event['attributes']['deviceRegistryLocation']
    projectId=event['attributes']['projectId']
    bquery=bigquery.Client()
    dataset_id="iotdata"
    table_id="weatherData"
    table_ref = bquery.dataset(dataset_id).table(table_id)
    table = bquery.get_table(table_ref)  # API request
    rows_to_insert = [
        (str(wd['sensorID']), wd['timecollected'], float(wd['temperature']), float(wd['pressure']), float(wd['humidity']), float(wd['dewpoint']))
    ]
    print(rows_to_insert)
    errors = bquery.insert_rows(table, rows_to_insert)  # API request
    assert errors == []

    if wd['predict']:
        instances=[]
        instance={}
        instance['temperature'] =  wd['temperature']
        instance['pressure'] =  wd['pressure']
        instance['humidity'] = wd['humidity'] 
        instance['dewpoint'] = wd['dewpoint'] 
        instances.append(instance)
    
        score = int(predict_json('ml-demo-212200', 'teste', instances, 'score')[0]['classes'][0])
        set_config(projectId, deviceRegistryLocation, deviceRegistryId, deviceId, score)
    

