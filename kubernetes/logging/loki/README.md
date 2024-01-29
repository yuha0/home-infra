```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm template -f helm/values.yaml -n logging --kube-version 1.28 loki grafana/loki-distributed > generated.yaml
```
