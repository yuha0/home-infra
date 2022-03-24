# External DNS

## Update helm based manifest

```bash
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update
helm template -f helm/values.yaml -n external-dns external-dns external-dns/external-dns > generated.yaml
```

## Update `helm/values.yaml` to a newer commit

```bash
# Go to the submodule dir and generate the diff file between our own version and the latest version
cd helm/external-dns
git pull
git diff --relative <curr-commit> <newer commit>  charts/external-dns/values.yaml > /tmp/values.diff

# Patch our values.yaml
cd ..
patch values.yaml /tmp/values.diff

# solve all the conflicts
```
