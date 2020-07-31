# Home Infra

> Just a pile of yaml files.

A Helm-free, opinionated GitOps repo for my homelab Kubernetes cluster.

## What do we have here

At this moment, I have the following up and running:

| component                                                        | comment                                                                               |
|------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome)       | Block ADs on DNS level                                                                |
| [metallb](https://github.com/metallb/metallb)                    | Bare metal load balancer in layer 2 mode                                              |
| [NGINX](https://github.com/kubernetes/ingress-nginx)             | Ingress controller to the infrastructure, open port 80 and 443 on the router for this |
| [cert-manager](https://github.com/jetstack/cert-manager)         | Manage Letsencrypt certificates for NGINX                                             |
| [plex](https://github.com/plexinc/pms-docker)                    | Watch videos and stuff                                                                |
| [home-bridge](https://github.com/nfarina/homebridge)             | Bridge for controlling Wi-Fi connected home appliances                                |
| [sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) | To hide secrets in Kubernetes                                                         |
| [wireguard](https://www.wireguard.com/)                          | WireGuard VPN, road-warrior style                                                     |
| [swagger-ui](https://github.com/swagger-api/swagger-ui)          | Browse API doc                                                                        |

Monitoring stack is Grafana, and Prometheus w/ Thanos.

## Limitations

1. Although I really want to get rid of docker, the cluster is deployed by [rke](https://github.com/rancher/rke), which only support docker as the CRI implementation.
2. AdGuard Home requires write permisison to the config file, but Kubernetes can only mount ConfigMap object as read-only (for good reasons). I had to do some weird dances with `initContainer` to use ConfigMap: https://github.com/AdguardTeam/AdGuardHome/issues/1964
3. qnap does not provide APIs to manage the storage, so I have to manage persistent volumes by hand like animals.
