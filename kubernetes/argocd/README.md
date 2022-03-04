```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm template -f helm/values.yaml --include-crds -n argocd argocd argo/argo-cd > generated.yaml
```
