# Kubernetes pods and nodes discovery and monitoring

Requirements:
- Python 3.6.8 or later
- VirtualEnv 15.1.0 or later
- 3rd party libraries for Python: kubernetes.


## Creating and activating VirtualEnv for Python:
```
mkdir /opt/virtualenv
cd /opt/virtualenv
virtualenv -p python3 kubernetes-monitoring
cd kubernetes-monitoring
source bin/activate
```


## Install Python dependencies using pip3:
```
pip3 install kubernetes
```


## Configuring access for user zabbix

The zabbix user must have enough privileges to read Kubernetes configurations
and access the Kubernetes objects. It is recommended that you create a context
that specifies the cluster, the user and the namespace that the monitoring
script will use when making calls to the API server. To achieve this, you need
to create a kubeconfig file. A kubekonfig file requires the URL of the API
server, a cluster CA certificate and credentials in the form of a key and a
certificate signed by the cluster CA.

This documentation provides steps to create certificates and how to have them
accepted by an existing Kubernetes cluster. If you already have existing
certificates and configurations, you may skip the first part where certificates
are created and approved. There is a template for the configuration file in case
you already have the certificates and you do not have a configuration file:
[There is an example file here](kubernetes_monitoring/config).


### Creating a certificate signing request (CSR) and retrieving certificates

First we run the OpenSSL command to generate new private key and CSR. You may
change the subject fields to suit your needs. Atleast the "/CN=zabbix"-field
should be checked since the role based access control (RBAC) sub-system will
determine the username from that field:
```
openssl req -new -newkey rsa:4096 -nodes -keyout zabbix.key -out zabbix.csr -subj "/C=FI/ST=Pirkanmaa/L=Tampere/O=Digia Oyj/OU=Digia Iiris/CN=zabbix"
```

Then we can retrieve the CSR-file and encode it using the base64 command:
```
cat zabbix.csr | base64 | tr -d '\n'
```

Then we paste the base 64 encoded CSR into the certificate signing request YAML-file.
[There is an example file here](kubernetes_monitoring/csr.yml).

Then we send the request to the API server:
```
kubectl create -f csr.yml
```

Then we check the condition of the request using the following command:
```
kubectl get csr
```

We should receive an output that is somewhat like this:
```
NAME     AGE   SIGNERNAME                            REQUESTOR       CONDITION
zabbix   10s   kubernetes.io/kube-apiserver-client   minikube-user   Pending
```

The next thing we need to do is approve the request:
```
kubectl certificate approve zabbix
```

When we check the status for the request again, the request should be approved:
```
kubectl get csr

NAME     AGE   SIGNERNAME                            REQUESTOR       CONDITION
zabbix   30s   kubernetes.io/kube-apiserver-client   minikube-user   Approved,Issued
```

Now that our request is approved, we can retrieve the certificate. We pipe the
output to base64 command for decoding and finally save it to a file:
```
kubectl get csr zabbix -o jsonpath='{.status.certificate}' | base64 --decode > zabbix.crt
```

Next thing we need is the cluster CA certificate. We pipe it to the base64
command for decoding and save it into a file as with the previous command:
```
kubectl get secret -o jsonpath="{.items[?(@.type==\"kubernetes.io/service-account-token\")].data['ca\.crt']}" | base64 --decode >ca.crt
```


### Setting up the configuration using existing certificates

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
kubectl config set-context zabbix --cluster=<cluster_name> --namespace=default --user=zabbix --kubeconfig=<config_file>
```

Specify the context for user zabbix:
```
kubectl config use-context zabbix --kubeconfig=<config_file>
```

Test configurations:
```
kubectl version --kubeconfig=<config_file>
```

You should now see a version listing from client and server, similar to the following:
```
Client Version: version.Info{Major:"1", Minor:"17", GitVersion:"v1.17.4", GitCommit:"<commit_hash>", GitTreeState:"clean", BuildDate:"2020-03-12T21:03:42Z", GoVersion:"go1.13.8", Compiler:"gc", Platform:"linux/amd64"}
Server Version: version.Info{Major:"1", Minor:"18", GitVersion:"v1.18.0", GitCommit:"<commit_hash>", GitTreeState:"clean", BuildDate:"2020-03-25T14:50:46Z", GoVersion:"go1.13.8", Compiler:"gc", Platform:"linux/amd64"}
```


### Authorize user to list pods, nodes, services and cron jobs from Kubernetes cluster.

[Example file for retrieving pods, nodes and services](kubernetes_monitoring/access.yml).
[Same example file as above but also includes cron jobs](kubernetes_monitoring/access-cron-jobs.yml).

```
kubectl create -f kubernetes_monitoring/access.yml
```




## Usage

Item Syntax | Description | Units |
----------- | ----------- | ----- |
kubernetes.discover.pods | Discover all Kubernetes pods | Provides the following template variables: {#POD}. Also provides service information in an array: ip, namespace, pod, restart_count, uptime. |
kubernetes.discover.pods.default | Discover all Kubernetes pods using default field selectors | Provides the following template variables: {#POD}. Also provides service information in an array: ip, namespace, pod, restart_count, uptime. |
kubernetes.discover.nodes | Discover all Kubernetes nodes | Provides the following template variables: {#NODE}. Also provides service information in an array: node, machine_id, status, system_uuid. |
kubernetes.discover.services | Discover all Kubernetes services | Provides the following template variables: {#SERVICE}. Also provides service information in an array: namespace, service, uid. |
kubernetes.discover.cronjobs | Discover all Kubernetes cron jobs | Provides the following template variables: {#CRONJOB}. Also provides cron job information in an array: completion_time, length, name, start_time, status, uid. |


## Retrieving data from discovery using JSONPath

In this example, data can be retrieved using JSONPath:
```
$.data[?(@.pod == "<pod>")].pod
$.data[?(@.pod == "<pod>")].restart_count

$.data[?(@.node == "<node>")].node
$.data[?(@.node == "<node>")].status

$.data[?(@.service == "<service>")].service
$.data[?(@.service == "<service>")].uid
```
