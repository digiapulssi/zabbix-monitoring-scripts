# Kubernetes pods and nodes discovery and monitoring

Requirements:
- Python 2.7.13 or Python 3.6.8
- 3rd party libraries for Python: kubernetes.


## For Python, install dependencies using pip:
```
pip install kubernetes
```


The zabbix user must have enough privileges to read Kubernetes configuration.

* Add read permission for user "zabbix" to directory "${HOME}/.kube/config" and to the certificates it contains.


## Usage

Item Syntax | Description | Units |
----------- | ----------- | ----- |
kubernetes.discover.pods | Discover all Kubernetes pods | Provides the following template variables: {#POD}. Also provides service information in an array: ip, namespace, pod, restart_count. |
kubernetes.discover.pods.default | Discover all Kubernetes pods using default field selectors | Provides the following template variables: {#POD}. Also provides service information in an array: ip, namespace, pod, restart_count. |
kubernetes.discover.nodes | Discover all Kubernetes nodes | Provides the following template variables: {#NODE}. Also provides service information in an array: node, machine_id, status, system_uuid. |
kubernetes.discover.services | Discover all Kubernetes services | Provides the following template variables: {#SERVICE}. Also provides service information in an array: namespace, service, uid. |


## Retrieving data from discovery using JSONPath

In this example, service data can be retrieved using JSONPath:
```
$.data[?(@.pod == "<pod>")].pod
$.data[?(@.pod == "<pod>")].restart_count

$.data[?(@.node == "<node>")].node
$.data[?(@.node == "<node>")].status

$.data[?(@.service == "<service>")].service
$.data[?(@.service == "<service>")].uid
```
