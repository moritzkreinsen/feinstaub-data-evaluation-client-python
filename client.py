import requests
from config import API_TOKEN

# TODO
# - create index in elastic
# - add schema for dataset using elasticsearch_dsl
# - add every sensordata-set with values normalized to fields to elastic
# - before doing http-call get newest dataset from elastic to speedup query to feinstaub-api by using timestamp_newer-GET-parameter


def get_data():
    header = {'Authorization': 'Token ' + API_TOKEN}
    session = requests.Session()
    url = "https://api.dusti.xyz/v1/node/"
    r = session.get(url, headers=header)
    for node in r.json():
        for sensor in node.get('sensors'):
            print("sensor_id: {}".format(sensor.get('id')))


if __name__ == '__main__':
    get_data()
