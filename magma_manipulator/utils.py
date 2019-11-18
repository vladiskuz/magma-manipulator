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
import os

import paramiko

import exceptions


LOG = logging.getLogger(__name__)
logging.getLogger("paramiko").setLevel(logging.WARNING)

CLOUD_INIT_CHECK_CMD = 'cloud-init status'
CLOUD_INIT_DONE = 'done'
CLOUD_INIT_RUNNING = 'running'

GET_GW_UUID_CMD = 'cd /var/opt/magma/docker ; '\
                  'sudo docker-compose exec '\
                  '-T magmad /usr/local/bin/show_gateway_info.py'

def is_gw_reachable(gw_ip):
    response = os.system('ping -c 1 ' + gw_ip)
    return response == 0


def exec_ssh_command(server, username, password, command):
    client = None
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        LOG.debug('Connection to server {server} '
                  'to execute command "{cmd}"'.format(server=server,
                                                      cmd=command))
        client.connect(server, username=username, password=password)
        ssh_stdin, ssh_stdout, ssh_stderr = client.exec_command(command)

        return ssh_stdout.read().decode('ascii')
    except Exception:
        msg = 'Something goes wrong during executing '\
              'ssh command "{cmd}" on server {server}'.format(cmd=command,
                                                              server=server)
        LOG.error(msg)
        raise exceptions.SshRemoteCommandException(msg)
    finally:
        if client:
            client.close()


def is_cloud_init_done(gw_ip, gw_username, gw_password):
    LOG.info('Check cloud-init status on gatewat {gw_ip}'.format(gw_ip=gw_ip))
    result = exec_ssh_command(gw_ip,
                              gw_username,
                              gw_password,
                              CLOUD_INIT_CHECK_CMD)
    LOG.info('Cloud-init status: {status} on gateway {gw_ip}'.format(
        status=result,
        gw_ip=gw_ip))
    if CLOUD_INIT_DONE in result:
        return True
    elif CLOUD_INIT_RUNNING in result:
        return False
    else:
        msg = 'Something goes wrong with cloud-init '\
              'on gateway: {error}'.format(error=result)
        LOG.error(msg)
        raise exceptions.CloudInitException(msg)


def get_gw_uuid_and_key(gw_ip, gw_username, gw_password):
    ssh_output = exec_ssh_command(gw_ip,
                                  gw_username,
                                  gw_password,
                                  GET_GW_UUID_CMD)
    gw_uuid = ssh_output.split('\n')[2]
    gw_key = ssh_output.split('\n')[6]
    return (gw_uuid, gw_key)
