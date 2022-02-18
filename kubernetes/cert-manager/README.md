```
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm template -f helm/values.yaml cert-manager jetstack/cert-manager --namespace cert-manager > generated.yaml
```
