# Argo CD

## Update helm based manifest

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm template -f helm/values.yaml --include-crds --kube-version 1.22.5 -n argocd argocd argo/argo-cd > generated.yaml
```

## Update `helm/values.yaml` to a newer commit

```bash
# Go to the submodule dir and generate the diff file between our own version and the latest version
cd helm/argocd-helm
git pull
git diff --relative <curr-commit> <newer commit>  charts/argo-cd/values.yaml > /tmp/values.diff

# Patch our values.yaml
cd ..
patch values.yaml /tmp/values.diff

# solve all the conflicts
```
