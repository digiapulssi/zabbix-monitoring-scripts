# Kubernetes pods and nodes discovery and monitoring

Requirements:
- Python 2.7.13 or Python 3.6.8
- Libraries for Python: kubernetes.


## For Python version 3, install dependencies using pip3:
```
pip3 install kubernetes
```


## For Python version 2, install dependencies using pip:
```
pip install kubernetes
```


The zabbix user must have enough privileges to read Kubernetes configuration.

* Add read permission for user "zabbix" to directory "${HOME}/.kube/config" and to the certificates it contains.


## Usage

Item Syntax | Description | Units |
----------- | ----------- | ----- |
kubernetes.discover.pods | Discover all Kubernetes pods | Provides the following template variables: {#POD}. Also provides service information in an array: namespace, ip. |


## Retrieving data from discovery using JSONPath

In this example, service data can be retrieved using JSONPath:
```

```
