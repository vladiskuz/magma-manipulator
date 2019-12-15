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

import os
from jsonschema import validate
import yaml

schema = """
    type: object
    properties:
      k8s:
        type: object
        properties:
          kubeconfig_path:
            type: string
          namespace:
            type: string
      orc8r_api_url:
        type: string
      magma_certs_path:
        type: array
      gateways:
        type: object
        properties:
          configs_dir:
            type: string
          username:
            type: string
          rsa_private_key_path:
            type: string
"""


def parse_config(cfg_rel_path):
    dirname = os.path.dirname(__file__)
    cfg_path = os.path.join(dirname, cfg_rel_path)
    with open(cfg_path, 'r') as ymlfile:
        yml_cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    validate(yml_cfg, yaml.load(schema))
    return yml_cfg


class Config(object):
    def __init__(self, yml_cfg):
        for k, v in yml_cfg.items():
            if isinstance(v, dict):
                self.__dict__[k] = Config(v)
            else:
                self.__dict__[k] = v


cfg = Config(parse_config('config.yml'))
