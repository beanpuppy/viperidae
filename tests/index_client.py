#!/usr/bin/env python

import requests
import base64
import json
import pprint

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from api.models import *


def authenticate(client):
    url           = 'http://0.0.0.0:8080/v1/auth'
    base64encoded = base64.b64encode(f'{client.client}:{client.secret}'.encode())
    header        = {'Authorization': f'Basic {base64encoded.decode()}'}
    payload       = {'grant_type': 'authorization_code'}

    post_request  = requests.post(url, data=payload, headers=header)
    response_data = json.loads(post_request.text)

    print('\nAuth response:')

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(response_data)

    return response_data


def index_site(client):
    print(f'Authenticating {client.name}...')

    response = authenticate(client)

    print(f'\nIndexing {client.website}...')

    url      = 'http://0.0.0.0:8080/v1/index'
    token    = response.get('access_token') # get access token
    header   = {'Authorization': f'Bearer {token}'}

    get_request   = requests.get(url, headers=header)
    response_data = json.loads(get_request.text)

    print('\nIndexed Pages: ')
    for page in response_data:
        print(page['uri'])

    print('\nFinished')


def get_client():
    name = input('Enter client name: ')
    try:
        return Client.get(Client.name == name)
    except: sys.exit(f'Error: Could not find client "{name}"')


if __name__ == '__main__':
    index_site(get_client())
