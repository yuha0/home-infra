```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm template -f helm/values.yaml -n monitoring monitoring prometheus-community/prometheus-node-exporter > generated.yaml
```
