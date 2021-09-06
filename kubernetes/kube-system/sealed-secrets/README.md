# Sealed Secrets Controller

## Configuration

`generated.yaml` is generated by `helm` and should not be modified directly. Modifications not supported by the chart should be done by kustomize patches.

## Update

```bash
helm template -f helm/values.yaml sealed-secrets-controller sealed-secrets/sealed-secrets > generated.yaml
```