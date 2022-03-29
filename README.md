# Home Infrastructure

Here's the infrastructure-as-code repository for my home infrastructure.

The whole infrastructure is running in a Kubernetes cluster, which is managed by [kubernetes-sigs/kubespray](https://github.com/kubernetes-sigs/kubespray) based Ansible playbooks [here](ansible/).

Everything else is running in the Kubernetes cluster and managed with [GitOps](https://www.weave.works/technologies/gitops/) concept leveraging [ArgoCD](https://argo-cd.readthedocs.io).

## Kubernetes GitOps Infra

### Components

| Name | Description | Sync Status |
| --- | --- | --- |
| [adguardhome](kubernetes/adguardhome) | [AdguardTeam/AdGuardHome](https://github.com/AdguardTeam/AdGuardHome) | ![sync-status](https://argocd.yuha0.com/api/badge?name=adguardhome&revision=true) |
| [apiserver](kubernetes/kube-system/apiserver) | A MetalLB managed load balancer for Kubernetes cluster API servers | ![sync-status](https://argocd.yuha0.com/api/badge?name=apiserver&revision=true) |
| [argocd](kubernetes/argocd) | [argoproj/argo-cd](https://github.com/argoproj/argo-cd) | ![sync-status](https://argocd.yuha0.com/api/badge?name=argocd&revision=true) |
| [cert-manager](kubernetes/cert-manager) | [cert-manager/cert-manager](https://github.com/cert-manager/cert-manager) | ![sync-status](https://argocd.yuha0.com/api/badge?name=cert-manager&revision=true) |
| [cloudflare-ddns](kubernetes/cloudflare-ddns) | [yuha0/cloudflare-ddns](https://github.com/yuha0/cloudflare-ddns) | ![sync-status](https://argocd.yuha0.com/api/badge?name=cloudflare-ddns&revision=true) |
| [external-dns](kubernetes/external-dns) | [kubernetes-sigs/external-dns](https://github.com/kubernetes-sigs/external-dns) | ![sync-status](https://argocd.yuha0.com/api/badge?name=external-dns&revision=true) |
| [external-service-accounts](kubernetes/kube-system/external-service-accounts) | cluster ervice accounts used by external services | ![sync-status](https://argocd.yuha0.com/api/badge?name=external-service-accounts&revision=true) |
| [grafana](kubernetes/grafana) | [grafana/grafana](https://github.com/grafana/grafana) | ![sync-status](https://argocd.yuha0.com/api/badge?name=grafana&revision=true) |
| [ingress-nginx-external](kubernetes/ingress-nginx/external) | internet facing instance of [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx) | ![sync-status](https://argocd.yuha0.com/api/badge?name=ingress-nginx-external&revision=true) |
| [ingress-nginx-internal](kubernetes/ingress-nginx/internal) | LAN instance of [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx) | ![sync-status](https://argocd.yuha0.com/api/badge?name=ingress-nginx-internal&revision=true) |
| [kube-state-metrics](kubernetes/kube-system/kube-state-metrics) | [kubernetes/kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) | ![sync-status](https://argocd.yuha0.com/api/badge?name=kube-state-metrics&revision=true) |
| [loki](kubernetes/logging/loki) | [grafana/loki](https://github.com/grafana/loki) | ![sync-status](https://argocd.yuha0.com/api/badge?name=loki&revision=true) |
| [metallb-system](kubernetes/metallb-system) | [metallb/metallb](https://github.com/metallb/metallb) | ![sync-status](https://argocd.yuha0.com/api/badge?name=metallb-system&revision=true) |
| [nfs-subdir](kubernetes/nfs-subdir) | [kubernetes-sigs/nfs-subdir-external-provisioner](https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner) | ![sync-status](https://argocd.yuha0.com/api/badge?name=nfs-subdir&revision=true) |
| [node-exporter](kubernetes/monitoring/node-exporter) | [prometheus/node_exporter](https://github.com/prometheus/node_exporter) | ![sync-status](https://argocd.yuha0.com/api/badge?name=node-exporter&revision=true) |
| [plex](kubernetes/plex) | [plexinc/pms-docker](https://github.com/plexinc/pms-docker) | ![sync-status](https://argocd.yuha0.com/api/badge?name=plex&revision=true) |
| [prometheus](kubernetes/monitoring/prometheus) | [prometheus/prometheus](https://github.com/prometheus/prometheus) | ![sync-status](https://argocd.yuha0.com/api/badge?name=prometheus&revision=true) |
| [prometheus-operator](kubernetes/monitoring/prometheus-operator) | [prometheus-operator/prometheus-operator](https://github.com/prometheus-operator/prometheus-operator) | ![sync-status](https://argocd.yuha0.com/api/badge?name=prometheus-operator&revision=true) |
| [promtail](kubernetes/logging/promtail) | [grafana/loki's promtail client](https://github.com/grafana/loki/tree/main/clients/pkg/promtail) | ![sync-status](https://argocd.yuha0.com/api/badge?name=promtail&revision=true) |
| [sealed-secrets](kubernetes/kube-system/sealed-secrets) | [bitnami-labs/sealed-secrets](https://github.com/bitnami-labs/sealed-secrets)| ![sync-status](https://argocd.yuha0.com/api/badge?name=sealed-secrets&revision=true) |
| [system-service-monitors](kubernetes/kube-system/system-service-monitors) | Prometheus Operator's service monitor instances for monitoring Kubernetes system components | ![sync-status](https://argocd.yuha0.com/api/badge?name=system-service-monitors&revision=true) |
| [tailscale](kubernetes/tailscale) | [tailscale/tailscale](https://github.com/tailscale/tailscale) | ![sync-status](https://argocd.yuha0.com/api/badge?name=tailscale&revision=true) |
| [thanos](kubernetes/monitoring/thanos) | [thanos-io/thanos](https://github.com/thanos-io/thanos) | ![sync-status](https://argocd.yuha0.com/api/badge?name=thanos&revision=true) |
| [unifi](kubernetes/unifi) | [Unifi Network Application](https://help.ui.com/hc/en-us/articles/1500012237441-UniFi-Network-Use-the-UniFi-Network-Application) with [Bitnami's MongoDB helm chart](https://github.com/bitnami/charts/tree/master/bitnami/mongodb) managed mongodb database | ![sync-status](https://argocd.yuha0.com/api/badge?name=unifi&revision=true) |
