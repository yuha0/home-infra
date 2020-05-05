# Home Infra

> Just a pile of yaml files.

Opinionated infrastructure for homelab, powered by ansible, containers and Kubernetes.

## Progress

At this moment, I have the following up and running:

| component                                                        | deploy         | comment                                                                             |
|------------------------------------------------------------------|----------------|-------------------------------------------------------------------------------------|
| [pi-hole](https://github.com/pi-hole/pi-hole)                    | docker-compose |                                                                                     |
| [metallb](https://github.com/metallb/metallb)                    | Kubernetes     | Bare metal load balancer in layer 2 mode                                            |
| [NGINX](https://github.com/kubernetes/ingress-nginx)             | Kubernetes     | The only ingress to the infrastructure, open port 80 and 443 on the router for this |
| [cert-manager](https://github.com/jetstack/cert-manager)         | Kubernetes     | Manage Letsencrypt certificates for NGINX                                           |
| [plex](https://github.com/plexinc/pms-docker)                    | Kubernetes     |                                                                                     |
| [home-bridge](https://github.com/nfarina/homebridge)             | Kubernetes     | Bridge for controlling Wi-Fi connected home appliances                              |
| [sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) | Kubernetes     | To hide secrets in Kubernetes                                                       |
| [qnap](https://www.qnap.com)                                     | manual         | Kubernetes persistent volume provider (NFS)                                         |
| [wireguard](https://www.wireguard.com/)                          | manual         | on-demand VPN to connect back home on the go                                        |

## Limitations

1. Although I really want to get rid of docker, the cluster is deployed by [rke](https://github.com/rancher/rke), which only support docker as the CRI implementation.
2. pi-hole cannot run in Kubernetes because I can't pull container images from internet without DNS.
3. qnap does not provide APIs to manage the storage, so I have to manage persistent volumes by hand like animals.

## Upcoming projects

* Visualize all my DNS queries on a map: [elk-hole](https://github.com/nin9s/elk-hole)
