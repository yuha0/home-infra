# MongoDB for Unifi Network Application

## Installation

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm template -f helm/values.yaml -n unifi unifi bitnami/mongodb > generated.yaml
```

## Operator vs vanilla StatefulSet

Kubernetes does not have good support for stateful workload like databases out of box. And typically, people use operators that understand stateful application states for orchestration/bootstraping. 

On the surface, it seems to make sense to use [MongoDB Kubernetes Operator](https://github.com/mongodb/mongodb-kubernetes-operator). It leverage official mongodb container images, which are multi-arch builds. This is quite important to me, since a bunch of Raspberry Pi boards is a big part of my infra. Bitnami's helm chart, on the other hand, [does not support multi-arch image](https://github.com/bitnami/charts/issues/7305).

However, using the mongodb community operator isn't order of magnitude better neither:

- My only use case for mongodb is the data backend for Unifi Network Application. This data isn't that valuable considering that I already have daily config export as a backup. In case of data corruption, instead of messing with MongoDB data recovery, it is easier to just import my backup to a brand new Unifi instance -- I will be back to business in minutes.
- The operator itself [does not have multi-arch build](https://github.com/mongodb/mongodb-kubernetes-operator/issues/299), so I eventually need to run something on an AMD64 box anyways.
- The [installation steps](https://github.com/mongodb/mongodb-kubernetes-operator/blob/master/docs/install-upgrade.md) are unnecessarily complicated. My goal is to manage the whole infra in a GitOps way, and I can't manually edit files and run `kubectl` commands in certain order.

The chart gives me a working MongoDB cluster, an easy path to receive future updates (helm). It is not production-grade reliable, but good enough.
