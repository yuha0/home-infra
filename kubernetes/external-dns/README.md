```bash
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update
helm template -f helm/values.yaml -n external-dns external-dns external-dns/external-dns > generated.yaml
```
