```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm template -f helm/values.yaml internal ingress-nginx/ingress-nginx --namespace ingress-nginx-internal > generated.yaml
```
