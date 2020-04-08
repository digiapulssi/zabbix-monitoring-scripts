# Kubernetes pods and nodes discovery and monitoring

Requirements:
- Python 2.7.13 or Python 3.6.8
- 3rd party libraries for Python: kubernetes.


## For Python, install dependencies using pip:
```
pip install kubernetes
```


## Configuring access for user zabbix

The zabbix user must have enough privileges to read Kubernetes configurations
and access the Kubernetes objects. It is recommended that you create a context
that specifies the cluster, the user and the namespace that the monitoring
script will use when making calls to the API server. To achieve this, you need
to create a kubeconfig file. A kubekonfig file requires the URL of the API
server, a cluster CA certificate and credentials in the form of a key and a
certificate signed by the cluster CA. This documentation does not provive steps
to create certificates or how to have them accepted by an exiting Kubernetes
cluster. It is assumed the certificates are generated beforehand and approved
by the cluster.

Retrieve cluster name:
```
kubectl config view -o jsonpath='{.clusters[0].name}'
```

Retrieve cluster server address:
```
kubectl config view -o jsonpath='{.clusters[0].cluster.server}'
```

Pull details from existing Kubernetes-configurations:
```
kubectl config set-cluster <cluster_name> --server=<server_address> --certificate-authority=<ca.crt> --kubeconfig=<config_file> --embed-certs
```

Set up the user:
```
kubectl config set-credentials zabbix --client-certificate=<certificate.crt> --client-key=<private.key> --kubeconfig=<config_file> --embed-certs
```

Create a context:
```
kubectl config set-context zabbix --cluster=<cluster_name> --namespace=<namespace> --user=zabbix --kubeconfig=<config_file>
```
The namespace-parameter defines what name is to be used for the context.

Create a namespace:
```
kubectl create ns <namespace>
```

Set label for namespace:
```
kubectl label ns <namepace> user=zabbix env=<environment_name>
```

Specify the context for user zabbix:
```
kubectl config use-context <namespace> --kubeconfig=<config_file>
```

Test configurations:
```
kubectl version --kubeconfig=<config_file>
```

You should now see a version listing from client and server. Next step is to give access for user to list pods, nodes and services from Kubernetes cluster.


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
