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

from kubernetes import client, config

LOG = logging.getLogger(__name__)


def get_gw_ip(kubeconfig_path, kube_namespace, gw_pod_name):
    config.load_kube_config(config_file=kubeconfig_path)
    v1 = client.CoreV1Api()

    LOG.info('Trying to get gateway IP adress for '
             '{gw_pod_name} from kubernetes'.format(gw_pod_name=gw_pod_name))
    pod = v1.read_namespaced_pod_status(gw_pod_name, kube_namespace)
    LOG.info('Gateway IP address ({gw_pod_name}) received '
             'from kubernetes: {gw_ip}'.format(gw_pod_name=gw_pod_name,
                                               gw_ip=pod.status.pod_ip))
    return pod.status.pod_ip


def is_pod_ready(kubeconfig_path, kube_namespace, gw_pod_name):
    config.load_kube_config(config_file=kubeconfig_path)
    v1 = client.CoreV1Api()

    result = v1.read_namespaced_pod_status(gw_pod_name, kube_namespace)
    for container in result.status.container_statuses:
        if not container.ready:
            LOG.info('Containers in pod {gw_pod_name} are not ready'.format(
                gw_pod_name=gw_pod_name))
            return False
    LOG.info('Containers in pod {gw_pod_name} are ready'.format(
        gw_pod_name=gw_pod_name))
    return True
