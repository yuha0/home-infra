```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm template -f helm/values.yaml -n promtail promtail grafana/promtail > generated.yaml
```
