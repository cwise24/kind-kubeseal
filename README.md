# ArgoCD

Deploy KinD cluster with Calico

```
kind create cluster --config kind-mk-config.yaml --name argocd
```

## View Cluster

```
kubectl get nodes
NAME                  STATUS     ROLES           AGE   VERSION
NAME                   STATUS   ROLES           AGE    VERSION
argocd-control-plane   Ready    control-plane   103m   v1.35.0
argocd-worker          Ready    <none>          102m   v1.35.0
argocd-worker2         Ready    <none>          102m   v1.35.0
```

## Install Calico

By default, *kind* comes with it's own cni called *kindnetd*. This has been disabled in *kind-mk-config.yaml* and Calico will be installed.


[KIND](https://www.tigera.io/project-calico/)

```
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.29.2/manifests/tigera-operator.yaml
```

**You'll need to run this as we've set a cusoter cidr block**:

```
kubectl apply -f calico-custom-resource.yaml
```

Verify Installation

```
watch kubectl get pods -l k8s-app=calico-node -A
```

>[!TIP]
> MacOS zsh does not have watch, brew install watch

# ArgoCD

Install ArgoCD 


Add **argo** repo:

```
helm repo add argo https://argoproj.github.io/argo-helm
```

Install ArgoCD:

```
helm install argocd argo/argo-cd --create-namespace -n argocd -f argo-values.yaml 
```

I'm passing a custom values file to attempt to bypass the *Lease* exclusion error by altering the default values and allocating the Argo Server NodePort so it does not have to be a manual process.

Output:

```
NAME: argocd
LAST DEPLOYED: Fri Feb  6 12:18:55 2026
NAMESPACE: argocd
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
In order to access the server UI you have the following options:

1. kubectl port-forward service/argocd-server -n argocd 8080:443

    and then open the browser on http://localhost:8080 and accept the certificate

2. enable ingress in the values file `server.ingress.enabled` and either
      - Add the annotation for ssl passthrough: https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/#option-1-ssl-passthrough
      - Set the `configs.params."server.insecure"` in the values file and terminate SSL at your ingress: https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/#option-2-multiple-ingress-objects-and-hosts


After reaching the UI the first time you can login with username: admin and the random password generated during the installation. You can find the password by running:

kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

(You should delete the initial secret afterwards as suggested by the Getting Started Guide: https://argo-cd.readthedocs.io/en/stable/getting_started/#4-login-using-the-cli)

```

Verify:

```
kubectl get po -n argocd
```

Retrieve the password from the secrets in argocd 

```
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d; echo
```

Now you can log into ArgoCD at [https://localhost:30080](https://localhost:30080)

Username: admin <br/>
Password: from above

![argo-login](imgs/argocd_login.png)

We will do changes from argocd cli 

# Git

Create lab ssh deploy keys

```
C.Wise@GJ4HFVQPGW ~ % ssh-keygen -t rsa -b 4096
Generating public/private rsa key pair.
Enter file in which to save the key (/Users/C.Wise/.ssh/id_rsa): /Users/C.Wise/.ssh/argo-lab
Enter passphrase for "/Users/C.Wise/.ssh/argo-lab" (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /Users/C.Wise/.ssh/argo-lab
Your public key has been saved in /Users/C.Wise/.ssh/argo-lab.pub
The key fingerprint is:
SHA256:biTgtco6VHDcoJa5WpSlQGnQaFKEyeu4kEdPevGNwNY C.Wise@GJ4HFVQPGW
The key's randomart image is:
+---[RSA 4096]----+
|*O+.oo           |
|=*oBo .          |
|+ X+...          |
| +.oBoE.         |
|ooo*.+ooS        |
|+++.o.o+.        |
|o+ .o   o        |
|. ..   .         |
|  ..             |
+----[SHA256]-----+
```

Paste the public key in the repository [kind-argo-repo](https://github.com/cwise24/kind-argo-repo). <br/>
From the repository, go to *Settings*:


![argo-settings](imgs/git_settings.png)

Down the left hand side click on *Deploy keys* to add your public key.

![deploy-key](imgs/git_deploykey.png)

Now you can move back to the ArgoCD ui to connect to the Github repository.

Add git repo to ArgoCD, click gear icon on left:

![repo-settings](imgs/repo_manage.png)

Click *Connect Repo*

![repo-connect](imgs/repo_connect.png)

Now open the Repositories blade:

![repo-add](imgs/repo_settings.png)

Now you must fill out the information for the repository. Notice the repository url, choose the *git@github.com:cwise24/kind-argo-repo.git*. You can get this from the repository site when you clone.

```
git@github.com:cwise24/kind-argo-repo.git
```

![repo-info](imgs/repo_info.png)

Also, take time to scroll and view all the options when setting up the repository.

![repo-connected](imgs/repo_connected.png)

You should now see the above screen.


# kubeseal and sealed secrets

[repo](https://github.com/bitnami-labs/sealed-secrets)

By default, this will run in the namespace *kube-system* and the below helm install commands will install there.

```
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
```

```
helm upgrade --install sealed-secrets sealed-secrets/sealed-secrets -n kube-system
```

Output:

```
Release "sealed-secrets" does not exist. Installing it now.
NAME: sealed-secrets
LAST DEPLOYED: Tue Feb 24 09:12:26 2026
NAMESPACE: kube-system
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
** Please be patient while the chart is being deployed **

You should now be able to create sealed secrets.

1. Install the client-side tool (kubeseal) as explained in the docs below:

    https://github.com/bitnami-labs/sealed-secrets#installation-from-source

2. Create a sealed secret file running the command below:

    kubectl create secret generic secret-name --dry-run=client --from-literal=foo=bar -o [json|yaml] | \
    kubeseal \
      --controller-name=sealed-secrets \
      --controller-namespace=kube-system \
      --format yaml > mysealedsecret.[json|yaml]

The file mysealedsecret.[json|yaml] is a commitable file.

If you would rather not need access to the cluster to generate the sealed secret you can run:

    kubeseal \
      --controller-name=sealed-secrets \
      --controller-namespace=kube-system \
      --fetch-cert > mycert.pem

to retrieve the public cert used for encryption and store it locally. You can then run 'kubeseal --cert mycert.pem' instead to use the local cert e.g.

    kubectl create secret generic secret-name --dry-run=client --from-literal=foo=bar -o [json|yaml] | \
    kubeseal \
      --controller-name=sealed-secrets \
      --controller-namespace=kube-system \
      --format [json|yaml] --cert mycert.pem > mysealedsecret.[json|yaml]

3. Apply the sealed secret

    kubectl create -f mysealedsecret.[json|yaml]

Running 'kubectl get secret secret-name -o [json|yaml]' will show the decrypted secret that was generated from the sealed secret.

Both the SealedSecret and generated Secret must have the same name and namespace.
```

## to remove

# Application

Add application, for this we will use the *envoy* directroy in argocd-repo. The envoy-gateway application will deploy envoy and the gateway api crds for use.
 

![add-application](imgs/application_add.png)

![app-create](imgs/application_create1.png)

![app-paste](imgs/application-paste.png)


Click create to finalize the creation process

![app-create-final](imgs/app-create2.png)

You can view the application by clicking the tile:

![view-app](imgs/app-view1.png)

This is the tree view where you can see all the components deployed, check out all the options in the top right. The views are:

Tree <br/>
Pods <br/>
Network <br/>
List <br/>

![tree-view](imgs/app-view-tree.png)

Pod view, from here you can see pod distribution, health. Hover over the pods to see details.

![app-pod-view](imgs/app-pod-view.png)

![app-pod-health](imgs/app-pod-health.png)

![app-pod-logs](imgs/app-pod-logs.png)

## ArgoCD cli 

[Install](https://foxutech.medium.com/argo-cd-cli-installation-and-commands-65ab578ed75) argocd-cli 

Linux:

```
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
```

Mac:

```
brew install argocd
```

Windows:

Download With PowerShell: Invoke-WebRequest

You can view the latest version of Argo CD at the link above or run the following command to grab the version:

```
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-cd/releases/latest).tag_name
```

Replace $version in the command below with the version of Argo CD you would like to download:

```
$url = "https://github.com/argoproj/argo-cd/releases/download/" + $version + "/argocd-windows-amd64.exe"
$output = "argocd.exe"
Invoke-WebRequest -Uri $url -OutFile $output
```

> Note: Also please note you will probably need to move the file into your PATH.


ArgoCD cli [guide](https://argo-cd.readthedocs.io/en/stable/user-guide/commands/argocd_login/)

change password [link](https://argo-cd.readthedocs.io/en/stable/getting_started/#4-login-using-the-cli)
show applications 

Log in:

```
argocd login localhost:30080 --username admin --password <Paste here> --insecure
```

```
Usage:
  argocd [flags]
  argocd [command]

Available Commands:
  account     Manage account settings
  admin       Contains a set of commands useful for Argo CD administrators and requires direct Kubernetes access
  app         Manage applications
  appset      Manage ApplicationSets
  cert        Manage repository certificates and SSH known hosts entries
  cluster     Manage cluster credentials
  completion  output shell completion code for the specified shell (bash, zsh or fish)
  context     Switch between contexts
  gpg         Manage GPG keys used for signature verification
  help        Help about any command
  login       Log in to Argo CD
  logout      Log out from Argo CD
  proj        Manage projects
  relogin     Refresh an expired authenticate token
  repo        Manage repository connection parameters
  repocreds   Manage repository connection parameters
  version     Print version information
  ```
List applications:

```
argocd app list
```

Set new admin password:

```
argocd account update-password --account admin --current-password 'admin_password' --new-password 'new_password'
```

## Lab

# Metal LB

```
docker inspect kind | jq .[].Status.IPAM.Subnets
```

Collect the node ip address range provided by the KinD CNI in your Docker network. We will use avaiable IP space from this subnet to use for IPAM for MetalLB

Make necessary edits to the metallb-conf.yaml file under the **IPAddressPool** section. You'll notice two files, IPAddrress Pool and advertisement (L2/L3).


```
---
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: ext-pool
  namespace: metal
spec:
  addresses:
  - 172.19.255.1-172.19.255.20
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: ext-advertisement
  namespace: metal
```

Now deploy the metal lb manifest:

```
kubetcl apply -f metallb-conf.yaml
```

Deploy metallb applcation *metallb-app.yaml* from ArgoCD

# Envoy 

[Video](https://www.youtube.com/watch?v=kDtcVB53U7o)

Deploy the Envoy application for Envoy Gateway. This will also add the necessary CRDs.

```
kubectl apply -f envoy-app.yaml
```

# Testing

Deploy *quickstart.yaml*

This file will deploy 

- Gateway Class
- Gateway
- Deployment
- Service
- HttpRoute

View services for Loadbalancer external IP

```
cwise@pop-os:~/Projects/GH/kind-envoy$ k get svc -n envoy-gateway-system
NAME                        TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)                                            AGE
envoy-default-eg-e41e7b31   LoadBalancer   10.96.125.225   172.19.255.1   80:32710/TCP                                       15m
envoy-gateway               ClusterIP      10.96.200.117   <none>         18000/TCP,18001/TCP,18002/TCP,19001/TCP,9443/TCP   16m
```


```
curl -H"Host: www.example.com" http://172.19.255.1/get -v
```

# Observability

[Link](https://gateway.envoyproxy.io/docs/tasks/observability/gateway-api-metrics/)

Deploy the Envoy Gateway Addon application:

```
kubectl apply -f envoy-addon-app.yaml
```

Then look for Grafana and Prometheus services in the *monitoring* namespace 

```
kubectl get svc -n monitoring
```

Your metallb should have provided IPs for these services.

Deploy the *backendtrafficpolicy*

whether targetRefs is httproute or gateway the cluster health log show httproute and pod service port, btp will find service attached to gateway or httproute (more specific) and will look for expected status, if pod is configured for hostname that will be passed too. So in this testing, only expected status is looked at for health. 

In short:

```
 kubectl get ep
```

to do:

- string

- configure hostname

will try tcp health probes

```
k apply -f envoy-cat-health.yaml
```

```
kubectl port-forward deploy/envoy-default-eg-e41e7b31 -n envoy-gateway-system 19000:19000
```

```
curl http://localhost:19000/clusters | grep health
```


# Fault btp

(https://gateway.envoyproxy.io/latest/api/extension_types/)

[Fault Injection](https://gateway.envoyproxy.io/docs/tasks/traffic/fault-injection)

```
kubectl apply -f btp-abort
```

```
hey -n 100 --host "www.nginx.com" http://172.19.255.1 
```

```
cwise@pop-os:~$ hey -n 100 -host "www.nginx.com" http://172.19.255.1

Summary:
  Total:	0.0564 secs
  Slowest:	0.0531 secs
  Fastest:	0.0002 secs
  Average:	0.0113 secs
  Requests/sec:	1773.2209
  
  Total data:	34038 bytes
  Size/request:	340 bytes

Response time histogram:
  0.000 [1]	|■
  0.006 [46]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  0.011 [13]	|■■■■■■■■■■■
  0.016 [19]	|■■■■■■■■■■■■■■■■■
  0.021 [3]	|■■■
  0.027 [10]	|■■■■■■■■■
  0.032 [0]	|
  0.037 [0]	|
  0.043 [1]	|■
  0.048 [0]	|
  0.053 [7]	|■■■■■■


Latency distribution:
  10% in 0.0007 secs
  25% in 0.0021 secs
  50% in 0.0086 secs
  75% in 0.0124 secs
  90% in 0.0254 secs
  95% in 0.0506 secs
  99% in 0.0531 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0045 secs, 0.0002 secs, 0.0531 secs
  DNS-lookup:	0.0000 secs, 0.0000 secs, 0.0000 secs
  req write:	0.0001 secs, 0.0000 secs, 0.0014 secs
  resp wait:	0.0057 secs, 0.0002 secs, 0.0128 secs
  resp read:	0.0000 secs, 0.0000 secs, 0.0009 secs

Status code distribution:
  [200]	54 responses
  [501]	46 responses

```
**Circuit Breaker**

Deploy circuit breaker, but notice this is against the Gateway (lowest precedence). You can deploy a *Gateway* level ckt breaker and a more specific HTTPRoute ckt breaker (higher precedence).

[Circuit Breaker directives](https://gateway.envoyproxy.io/latest/api/extension_types/#circuitbreaker)

You will target the *www.example.com* application. 

```
kubectl apply -f btp-ckt.yaml
```

You'll now use the load test to also add delay in the response:

```
hey -n 1000 -c 1000 -host "www.example.com" http://172.19.255.1/?delay=10s
```

```
cwise@pop-os:~$ hey -n 1000 -c 1000 -host "www.example.com" http://172.19.255.1/?delay=10s

Summary:
  Total:	15.0993 secs
  Slowest:	15.0932 secs
  Fastest:	10.0438 secs
  Average:	14.8511 secs
  Requests/sec:	66.2281
  
  Total data:	44500 bytes
  Size/request:	44 bytes

Response time histogram:
  10.044 [1]	|
  10.549 [40]	|■■
  11.054 [0]	|
  11.559 [0]	|
  12.064 [0]	|
  12.568 [0]	|
  13.073 [0]	|
  13.578 [0]	|
  14.083 [0]	|
  14.588 [0]	|
  15.093 [959]	|■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■


Latency distribution:
  10% in 15.0233 secs
  25% in 15.0356 secs
  50% in 15.0537 secs
  75% in 15.0746 secs
  90% in 15.0869 secs
  95% in 15.0901 secs
  99% in 15.0926 secs

Details (average, fastest, slowest):
  DNS+dialup:	0.0358 secs, 10.0438 secs, 15.0932 secs
  DNS-lookup:	0.0000 secs, 0.0000 secs, 0.0000 secs
  req write:	0.0002 secs, 0.0000 secs, 0.0192 secs
  resp wait:	14.8043 secs, 10.0400 secs, 15.0284 secs
  resp read:	0.0001 secs, 0.0000 secs, 0.0014 secs

Status code distribution:
  [200]	41 responses
  [504]	959 responses
```


**Load Balancer**

```
kubectl apply -f btp-lb.yaml
```

```
kubectl dealte po --all
```

```
hey -n 100 -c 100 --host "www.nginx.com" http://172.19.255.1
```

```
kubectl get po -l app=nginx --no-headers -o custom-columns=":metadata.name" | while read -r pod; do echo "$pod: received $(($(kubectl logs $pod | wc -l) -2)) requests"; done
```

##


# Clean Up

```
kind delete cluster --name argocd
```
