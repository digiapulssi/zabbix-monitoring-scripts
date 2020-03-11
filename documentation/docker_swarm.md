# Docker Swarm service discovery and monitoring

Requirements:
- Python 2.7.13 or Python 3.6.8
- Libraries for Python: docker, requests, urllib3.


## For Python version 3, install dependencies using pip:
```
pip3 install docker requests urllib3
```


## For Python version 2, install specific versions of libraries:
```
pip install docker==2.7.0 requests==2.23.0 urllib3==1.24.3
```


The zabbix user must have enough privileges to monitor docker

* Add zabbix user to docker group `sudo usermod -aG docker zabbix`


## Usage

Item Syntax | Description | Units |
----------- | ----------- | ----- |
docker.swarm.discover.services | Discover all running Docker services | Provides the following template variables: {#SERVICE}. Also provides service information in an array: hostname, status, uptime. |
docker.swarm.hostname | Retrieve hostname(s) for specified service. | Hostname(s) as a comma separated list. |
docker.swarm.status | Current service status. | String containing either "running" or "not running". |
docker.swarm.uptime | Retrieve uptime for specified service. | Seconds. |


## Retrieving data from discovery using JSONPath

In this example, service hostname can be retrieved using JSONPath:
```
$.data[?(@.service == "<service_name>")].hostname
```
