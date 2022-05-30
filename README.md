# Home Infrastructure

Here's the infrastructure-as-code repository for my home infrastructure.

The whole infrastructure is running in a Kubernetes cluster, which is managed by [kubernetes-sigs/kubespray](https://github.com/kubernetes-sigs/kubespray) based Ansible playbooks [here](ansible/).

Everything else is running in the Kubernetes cluster and managed with [GitOps](https://www.weave.works/technologies/gitops/) concept leveraging [ArgoCD](https://argo-cd.readthedocs.io).

## Kubernetes GitOps Infra

### Components

| Name | Description |
| --- | --- |
| [adguardhome](kubernetes/adguardhome) | [AdguardTeam/AdGuardHome](https://github.com/AdguardTeam/AdGuardHome) |
| [apiserver](kubernetes/kube-system/apiserver) | A MetalLB managed load balancer for Kubernetes cluster API servers |
| [argocd](kubernetes/argocd) | [argoproj/argo-cd](https://github.com/argoproj/argo-cd) |
| [cert-manager](kubernetes/cert-manager) | [cert-manager/cert-manager](https://github.com/cert-manager/cert-manager) |
| [cloudflare-ddns](kubernetes/cloudflare-ddns) | [yuha0/cloudflare-ddns](https://github.com/yuha0/cloudflare-ddns) |
| [external-dns](kubernetes/external-dns) | [kubernetes-sigs/external-dns](https://github.com/kubernetes-sigs/external-dns) |
| [external-service-accounts](kubernetes/kube-system/external-service-accounts) | cluster service accounts used by external services |
| [grafana](kubernetes/grafana) | [grafana/grafana](https://github.com/grafana/grafana) |
| [ingress-nginx-external](kubernetes/ingress-nginx/external) | Internet facing instance of [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx) |
| [ingress-nginx-internal](kubernetes/ingress-nginx/internal) | Local-only instance of [kubernetes/ingress-nginx](https://github.com/kubernetes/ingress-nginx) |
| [kube-state-metrics](kubernetes/kube-system/kube-state-metrics) | [kubernetes/kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) |
| [loki](kubernetes/logging/loki) | [grafana/loki](https://github.com/grafana/loki) |
| [metabase](kubernetes/metabase) | [metabase/metabase](https://github.com/metabase/metabase) |
| [metallb-system](kubernetes/metallb-system) | [metallb/metallb](https://github.com/metallb/metallb) |
| [nfs-subdir](kubernetes/nfs-subdir) | [kubernetes-sigs/nfs-subdir-external-provisioner](https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner) |
| [node-exporter](kubernetes/monitoring/node-exporter) | [prometheus/node_exporter](https://github.com/prometheus/node_exporter) |
| [plex](kubernetes/plex) | [plexinc/pms-docker](https://github.com/plexinc/pms-docker) |
| [prometheus](kubernetes/monitoring/prometheus) | [prometheus/prometheus](https://github.com/prometheus/prometheus) |
| [prometheus-operator](kubernetes/monitoring/prometheus-operator) | [prometheus-operator/prometheus-operator](https://github.com/prometheus-operator/prometheus-operator) |
| [promtail](kubernetes/logging/promtail) | [grafana/loki's promtail client](https://github.com/grafana/loki/tree/main/clients/pkg/promtail) |
| [sealed-secrets](kubernetes/kube-system/sealed-secrets) | [bitnami-labs/sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) |
| [system-service-monitors](kubernetes/kube-system/system-service-monitors) | Prometheus Operator's service monitor instances for monitoring Kubernetes system components |
| [tailscale](kubernetes/tailscale) | [tailscale/tailscale](https://github.com/tailscale/tailscale) |
| [thanos](kubernetes/monitoring/thanos) | [thanos-io/thanos](https://github.com/thanos-io/thanos) |
| [unifi](kubernetes/unifi) | [Unifi Network Application](https://help.ui.com/hc/en-us/articles/1500012237441-UniFi-Network-Use-the-UniFi-Network-Application) with [Bitnami's MongoDB helm chart](https://github.com/bitnami/charts/tree/master/bitnami/mongodb) managed mongodb database |
