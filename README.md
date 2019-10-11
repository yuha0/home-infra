# Home Infra

> Just a pile of yaml files.

Opinionated infrastructure for homelab, powered by ansible, containers and Kubernetes.

## Progress

At this moment, I have the following up and running:

| component                                                 | deploy method                 | comment                                                                             | TODO                                     |
|-----------------------------------------------------------|-------------------------------|-------------------------------------------------------------------------------------|------------------------------------------|
| [pi-hole](https://github.com/pi-hole/pi-hole)             | docker-compose                |                                                                                     | Move to Kubernetes                       |
| [NGINX](https://github.com/kubernetes/ingress-nginx)      | Kubernetes ingress controller | The only ingress to the infrastructure, open port 80 and 443 on the router for this |                                          |
| [cert-manager](https://github.com/jetstack/cert-manager)  | Kubernetes operator           | Manage Letsencrypt certificates for NGINX                                           |                                          |
| [plex](https://github.com/plexinc/pms-docker)             | Kubernetes deployment         |                                                                                     |                                          |
| [home-bridge](https://github.com/nfarina/homebridge)      | Kubernetes deployment         | Bridge for controlling Wi-Fi connected home appliances                              | Manage devices as CRDs with an operator? |
| [qnap](https://www.qnap.com)                              | manual                        | Kubernetes persistent volume provider (NFS)                                         |                                          |
| [wireguard](https://www.wireguard.com/)                   | manual                        | on-demand VPN to connect back home on the go                                        | Use Ansible to configure                 |

## Upcoming projects

* Visualize all my DNS queries on a map: [elk-hole](https://github.com/nin9s/elk-hole)
