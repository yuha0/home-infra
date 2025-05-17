# QNAP CSI Driver

For several reasons I need iscsi based persistent volumes:

- The [generic NFS driver](../csi-driver-nfs) is not performant enough for me for latency sensitive workloads like databases.
- QNAP's native object storage system, QuObject, running on a decade-old NAS, does not work for my scale that it rate-limits Thanos too much.
    - I am always inclined to treat the NAS appliance as a dumb storage system. Running this QuObject app on it is difficult to manage. It does not scale, can't easily manage TLS certificates, can't be configured programmatically (IAC).

QNAP offers a [Trident](https://github.com/NetApp/trident) based CSI driver: https://github.com/qnap-dev/QNAP-CSI-PlugIn. And this is a POC for myself to learn how it works. At this moment I don't have a dedicated storage pool and can't use it for real.

## Why is this so complicated?

QNAP's project README seems to be simple enough -- you install the operator, which installs the driver, and then add a configuration and it's done. But as I read the manifests there are a bunch of red flags that I need to make some workarounds:

- [Sometimes they replaced](https://github.com/qnap-dev/QNAP-CSI-PlugIn/commit/0efdda24ebc37f0b0370e14362e45eeb520f824c) images with some random personal images.
    - In my deployment I peg specific upstream commit. Every future version bump needs careful review.
- Bad RBAC makes me feel like no one cares about security
    - The operator [can read all secrets in all namespaces in the cluster](https://github.com/qnap-dev/QNAP-CSI-PlugIn/blob/a4ab67112b3d6fc3a07a48e800cf64a924fcac72/Helm/trident/templates/bundle.yaml#L73). Why do you need that? This software only needs to read a few secrets known to the deployer, all in a single namespace.
    - The operator [can create pods in any namespace](https://github.com/qnap-dev/QNAP-CSI-PlugIn/blob/a4ab67112b3d6fc3a07a48e800cf64a924fcac72/Helm/trident/templates/bundle.yaml#L100) and [exec into any pods](https://github.com/qnap-dev/QNAP-CSI-PlugIn/blob/a4ab67112b3d6fc3a07a48e800cf64a924fcac72/Helm/trident/templates/bundle.yaml#L306). Again, this means the operator can basically get any data from any pods in the cluster.
    - The most intereseting part is that the operator [can even create any clusterrole and bind it to anything](https://github.com/qnap-dev/QNAP-CSI-PlugIn/blob/a4ab67112b3d6fc3a07a48e800cf64a924fcac72/Helm/trident/templates/bundle.yaml#L339-L349). This is basically a cluster admin with no restriction. From Trident code, looks like the operator just dynamically generates clusterrole for the controller.
    - All these issues seem to come from [the upstream Trident project](https://github.com/NetApp/trident/blob/45f3cbc77586aeb263d8c1b617d33c01ac7b0edd/deploy/clusterrole.yaml). It's probably acceptable in some enterprise settings, but definitely not something I am comfortable to deploy to my homelab.
    - workarounds:
        - create a namespaced role, and move some permissions from the clusterrole to it, so that, for example, instead of accessing secrets cluster-wide, it can only access secrets in its own namespace.
        - spin up a vcluster and deploy an unmodified version as is, to get the generated clusterrole for the controller. Download the clusterrole manifest, repeat above sanitization step, and manage it with GitOps. This way the operator no longer needs the permission to create clusterroles.
