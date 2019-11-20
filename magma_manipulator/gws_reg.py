#!/usr/bin/env python3

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

import logging
import sys
import threading
import time
from queue import Queue
import yaml

from kubernetes import client, config, watch

import exceptions
import k8s_tools
import magma_tools
import utils


LOG = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

K8S_STARTED_REASON = ('Started',)
K8S_ADDED_TYPE = ('ADDED',)

events_queue = Queue()
INIT_QUEUE_TIMEOUT = 10
EVENT_MAX_TIMEOUT = 900


def watch_for_gateways(kubeconfig_path, kube_namespace, gw_names):
    config.load_kube_config(config_file=kubeconfig_path)
    v1 = client.CoreV1Api()
    w = watch.Watch()
    # infinity loop for k8s events
    for event in w.stream(v1.list_namespaced_event, kube_namespace, timeout_seconds=0):
        pod_name_prefix = event['object'].involved_object.name.split('-')[0]
        if pod_name_prefix in gw_names:
            if event['type'] in K8S_ADDED_TYPE and event['object'].reason in K8S_STARTED_REASON:
                LOG.info('Received event from k8s: {type} {name} {reason} '
                         '{timestamp} {msg}'.format(
                             type=event['type'],
                             name=event['object'].involved_object.name,
                             reason=event['object'].reason,
                             timestamp=event['object'].first_timestamp,
                             msg=event['object'].message))
                event = {
                    'pod_name': event['object'].involved_object.name,
                    'timeout': INIT_QUEUE_TIMEOUT
                }
                events_queue.put(event)


def start_kubernetes_event_handler(kubeconfig_path, kube_namespace, gw_names):
    LOG.info('Start watch for k8s events')
    watch_thread = threading.Thread(
        target=watch_for_gateways,
        args=(kubeconfig_path, kube_namespace, gw_names))
    watch_thread.start()


def put_event_after_timeout(event):
    LOG.debug('Wait {sec} seconds for event {event}'.format(
        sec=event['timeout'], event=event['pod_name']))
    if event['timeout'] > EVENT_MAX_TIMEOUT:
        LOG.error('Can not handle event for pod {pod_name}. Timeout expired'
                  .format(pod_name=event['pod_name']))
        return
    t = threading.Timer(event['timeout'], lambda: events_queue.put(event))
    t.start()


def parse_config(config):
    with open(config, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg


def main():
    cfg = parse_config('config.yml')
    start_kubernetes_event_handler(cfg['k8s']['kubeconfig_path'],
                                   cfg['k8s']['namespace'],
                                   cfg['gateways']['names'])
    while True:
        try:
            if not events_queue.empty():
                event = events_queue.get()
                gw_pod_name = event['pod_name']
                k8s_cfg = cfg['k8s']['kubeconfig_path']
                k8s_namespace = cfg['k8s']['namespace']

                LOG.info('Handle event for {gw_pod_name}'.format(
                    gw_pod_name=gw_pod_name))

                if not k8s_tools.is_pod_ready(k8s_cfg, k8s_namespace, gw_pod_name):
                    event['timeout'] *= 2
                    put_event_after_timeout(event)
                    continue

                gw_name = gw_pod_name.split('-')[0]
                gw_ip = k8s_tools.get_gw_ip(k8s_cfg,
                                            k8s_namespace,
                                            gw_pod_name)

                if not utils.is_gw_reachable(gw_ip):
                    event['timeout'] *= 2
                    put_event_after_timeout(event)
                    continue

                gw_username = cfg['gateways']['username']
                gw_password = cfg['gateways']['password']
                if not utils.is_cloud_init_done(gw_ip, gw_username, gw_password):
                    event['timeout'] *= 2
                    put_event_after_timeout(event)
                    continue

                # get gw hardware id and challenge key
                gw_uuid, gw_key = utils.get_gw_uuid_and_key(gw_ip,
                                                            gw_username,
                                                            gw_password)
                orc8r_api_url = cfg['orc8r_api_url']
                gw_net = cfg['gateways']['network']
                certs = cfg['magma_certs_path']
                if not magma_tools.is_network_exist(orc8r_api_url, gw_net, certs):
                    magma_tools.create_network(orc8r_api_url, gw_net, certs)

                gw_id = cfg['gateways']['id_prefix'] + gw_name
                if magma_tools.is_gateway_in_network(orc8r_api_url, gw_net, gw_id, certs):
                    magma_tools.delete_gateway(orc8r_api_url, gw_net, gw_id, certs)

                magma_tools.register_gw(orc8r_api_url,
                                        gw_net, gw_id, gw_uuid, gw_key, gw_name, certs)
            time.sleep(1)
        except Exception as e:
            LOG.error(e)

if __name__ == '__main__':
    sys.exit(main())
