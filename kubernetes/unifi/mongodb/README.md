```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm template -f helm/values.yaml -n unifi unifi bitnami/mongodb > generated.yaml
```
