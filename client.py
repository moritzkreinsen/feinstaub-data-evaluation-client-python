import json
import decimal
from config import API_TOKEN
from contextlib import suppress
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, RequestError
from elasticsearch_dsl import Search
import click
import requests


es = Elasticsearch(["elasticsearch"])
ES_INDEX_NAME = "feinstaub"


def delete_element_in_aggregator(_id):
    with suppress(ValueError, NotFoundError):
        es.delete(
            index=ES_INDEX_NAME,
            id=_id,
            doc_type="sensordata",
        )


def add_element_to_elastic(element):
    delete_element_in_aggregator(element.get('id'))

    if not es.indices.exists(index=ES_INDEX_NAME):
        es.indices.create(index=ES_INDEX_NAME)

    try:
        es.index(
            index=ES_INDEX_NAME,
            id=element.get('id'),
            doc_type="sensor_data",
            body=element,
        )
    except RequestError:
        pass


def get_newest(sensor_id):
    # FIXME: doc_type doesn't work :(
    #        .query("match", doc_type="sensordata")\
    s = Search(using=es, index=ES_INDEX_NAME)\
        .query("match", sensor_id=sensor_id)\
        .sort("-timestamp")
    response = s.execute()
    if response.hits:
        return response.hits[0].timestamp
    return None


@click.command()
@click.option('--sensor_id')
@click.option('--allsensors/--not-allsensors', default=False)
def get_data(allsensors, sensor_id=0):
    if allsensors:
        with open("sensor_list", "r") as fp:
            for line in fp.readlines():
                _get_data(line.strip())
        return
    else:
        _get_data(sensor_id)


def _get_data(sensor_id):
    sensor_id = int(sensor_id)
    header = {'Authorization': 'Token ' + API_TOKEN}
    session = requests.Session()
    url = "https://api.dusti.xyz/v1/data/"
    params = {
        'sensor': sensor_id,
        'page_size': 100
    }
    timestamp = get_newest(sensor_id)
    if timestamp:
        params.update({
            'timestamp_newer': timestamp
        })
    while url:
        r = session.get(url, headers=header, params=params)
        try:
            data = r.json()
        except json.decoder.JSONDecodeError:
            break
        url = data.get('next')
        if 'results' not in data:
            break
        for sensordata in data.get('results'):
            values = {}
            for value in sensordata.get('sensordatavalues'):
                try:
                    values[value['value_type']] = decimal.Decimal(value['value'])
                except decimal.InvalidOperation:
                    values = {}
                    break
            if values:
                element = {
                    'id': sensordata.get('id'),
                    'sensor_id': sensor_id,
                    'timestamp': sensordata.get('timestamp'),
                    'values': values
                }
                add_element_to_elastic(element)


def update_list_of_ppds():
    header = {'Authorization': 'Token ' + API_TOKEN}
    session = requests.Session()
    url = "https://api.dusti.xyz/v1/node/"
    params = {}
    r = session.get(url, headers=header, params=params)
    data = r.json()
    list_of_ppds = []
    for node in data:
        for sensor in node.get('sensors'):
            sensor_type = sensor.get("sensor_type", {})
            if sensor_type.get('name') == "PPD42NS":
                list_of_ppds.append(sensor.get('id'))
    with open("sensor_list", "w") as fp:
        for ppd in list_of_ppds:
            fp.write("{}\n".format(ppd))

if __name__ == '__main__':
#    update_list_of_ppds()
    get_data()
