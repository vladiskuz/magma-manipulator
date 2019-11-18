# Copyright 2019 Mirantis Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import logging
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urljoin

import exceptions

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
LOG = logging.getLogger(__name__)


def is_network_exist(orc8r_api_url, gw_net, certs):
    LOG.info('Check if network {gw_net} exists'.format(gw_net=gw_net))
    magma_net_url = urljoin(orc8r_api_url,
                            'magma/networks/{gw_net}'.format(gw_net=gw_net))
    LOG.debug('Make get request to {url}'.format(url=magma_net_url))
    resp = requests.get(magma_net_url, verify=False, cert=certs)
    str_result = resp.content.decode('ascii')
    json_result = json.loads(str_result)
    LOG.debug('Received result {result}'.format(result=json_result))
    if 'name' in json_result:
        return json_result['name'] == gw_net
    return False


def create_network(orc8r_api_url, gw_net, certs):
    LOG.info('Start to create network {gw_net}'.format(gw_net=gw_net))
    magma_net_url = urljoin(
        orc8r_api_url,
        'magma/networks?requested_id={gw_net}'.format(gw_net=gw_net))
    data = {
        'features': {
            'featureName': 'featureProp1',
            'featureName2': 'featureProp2'
        },
        'name': gw_net
    }
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    resp = requests.post(magma_net_url,
                         data=json.dumps(data),
                         headers=headers,
                         verify=False,
                         cert=certs)
    msg = 'Receive response {text} with status code {status_code} afte network'\
          '{gw_net} creation.'.format(text=resp.text,
                                      status_code=resp.status_code,
                                      gw_net=gw_net)
    LOG.info(msg)
    if resp.status_code not in [200, 201, 204]:
        raise exceptions.MagmaRequestException(msg)


def register_gw(orc8r_api_url, gw_net, gw_id, gw_uuid, gw_key, gw_name, certs):
    LOG.info('Register gateway {gw_name} in network '
             '{gw_net} with gateway id {gw_id}'.format(gw_name=gw_name,
                                                       gw_net=gw_net,
                                                       gw_id=gw_id))
    LOG.debug('Register gateway UUID {gw_uuid}, Gateway key {gw_key}'.format(
        gw_uuid=gw_uuid, gw_key=gw_key))
    magma_gw_url = urljoin(
        orc8r_api_url,
        'magma/networks/{gw_net}/gateways?requested_id={gw_id}'.format(
            gw_net=gw_net,
            gw_id=gw_id))
    data = {
        'hardware_id': gw_uuid,
        'key': {
            'key': gw_key,
            'key_type': 'SOFTWARE_ECDSA_SHA256'
        },
    }
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    resp = requests.post(magma_gw_url,
                         data=json.dumps(data),
                         headers=headers,
                         verify=False,
                         cert=certs)
    msg = 'Receive response {text} with status code {status_code} '\
          'after {gw_name} creation'\
          .format(text=resp.text,
                  status_code=resp.status_code,
                  gw_name=gw_name)
    LOG.info(msg)
    if resp.status_code not in [200, 201, 204]:
        raise exceptions.MagmaRequestException(msg)


def is_gateway_in_network(orc8r_api_url, gw_net, gw_id, certs):
    LOG.info('Check if gateway {gw_id} exists in network {gw_net}'.format(
        gw_id=gw_id, gw_net=gw_net))
    magma_gw_url = urljoin(
        orc8r_api_url,
        'magma/networks/{gw_net}/gateways'.format(
            gw_net=gw_net))
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    resp = requests.get(magma_gw_url,
                        headers=headers,
                        verify=False,
                        cert=certs)
    data = json.loads(resp.content.decode('ascii'))
    LOG.info('Gateways {gws} presented in network {gw_net}'.format(
        gws=data, gw_net=gw_net))
    return gw_id in data


def delete_gateway(orc8r_api_url, gw_net, gw_id, certs):
    LOG.info('Delete gateway {gw_id} in network {gw_net}'.format(
        gw_id=gw_id,
        gw_net=gw_net))

    magma_gw_url = urljoin(
        orc8r_api_url,
        'magma/networks/{gw_net}/gateways/{gw_id}'.format(
            gw_net=gw_net,
            gw_id=gw_id))
    headers = {'content-type': 'application/json',
               'accept': 'application/json'}
    resp = requests.delete(magma_gw_url,
                           headers=headers,
                           verify=False,
                           cert=certs)
    msg = 'Received response {text} with status code {status_code} '\
          'after gateway {gw_id} deletion'\
          .format(text=resp.text,
                  status_code=resp.status_code,
                  gw_id=gw_id)
    LOG.info(msg)
    if resp.status_code not in [200, 201, 204]:
        raise exceptions.MagmaRequestException(msg)
