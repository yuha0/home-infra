# Sealed Secrets Controller

## Configuration

`generated.yaml` is generated by `helm` and should not be modified directly. Modifications not supported by the chart should be done by kustomize patches.

## Update

```bash
helm template -f helm/values.yaml --include-crds sealed-secrets-controller sealed-secrets/sealed-secrets > generated.yaml
```

## Update `helm/values.yaml` to a newer commit

```bash
# Go to the submodule dir and generate the diff file between our own version and the latest version
cd helm/sealed-secrets
git pull
git diff --relative <curr-commit> <newer commit> helm/sealed-secrets/values.yaml > /tmp/values.diff

# Patch our values.yaml
cd ..
patch values.yaml /tmp/values.diff

# solve all the conflicts
```
