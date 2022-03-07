```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm template -f helm/values.yaml -n loki loki grafana/loki-distributed > generated.yaml
```
