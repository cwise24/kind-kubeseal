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
