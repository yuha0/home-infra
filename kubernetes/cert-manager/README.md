# Cert Manager

## Update helm based manifest

```
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm template --kube-version 1.28 -f helm/values.yaml cert-manager jetstack/cert-manager --namespace cert-manager > generated.yaml
```

## Update `helm/values.yaml` to a newer commit

```bash
# Go to the submodule dir and generate the diff file between our own version and the latest version
cd helm/cert-manager
git pull
git diff --relative 5c857d3737ecadd093350fb0a145ee9e3d2623fa be15ce2279b84cb2deb6f25c93aecb9679ff4c32  deploy/charts/cert-manager/values.yaml > /tmp/values.diff

# Patch our values.yaml
cd ..
patch values.yaml /tmp/values.diff

# solve all the conflicts
```
