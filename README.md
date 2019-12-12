# Magma manipulator
This is a magma gateway registration tool. Often we are faced with a situation where some magma pods with gateways are recreated, and we need to re-register them in magma by hand. This is normal when we are dealing with couple gateways, but when we have tens or hundreds of gateways, this operation takes a lot of time. This tool is trying to solve this problem.

## Installation
```
git clone git@github.com:vladiskuz/magma-manipulator.git
cd magma-manipulator
virtualenv -p python3 .venv
source .venv/bin/activate
python3 setup.py develop
```

## Configuration
* change *config.yml* for your purposes
* change *kconfig* regarding your k8s cluster
* run the tool magma-manipulator
* delete some pod and wait until the pod will recreate and this tool will re-register them in NMS

