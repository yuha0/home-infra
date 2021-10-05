```
helm repo add k8s-at-home https://k8s-at-home.com/charts
helm repo update
helm template -f helm/values.yaml -n unifi unifi k8s-at-home/unifi > generated.yaml
```
