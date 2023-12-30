# cloudnative-pg

Upstream manifests/helm chart create clusterroles with cluster wide permissions that are probably too wide(e.g.: all verbs on secrets in all namespaces). I sync a copy of upstream release manifest in the `base` directory, leverage kustomize patches to delete the rbac parts, and add custom role/clusterrole with more restricted access in `rbac.yaml`. Specifically:

- For namespaced resources, keep only `list` and `watch` verbs in the cluster role, and move everything else into a namespaced role in `cnpg-system` namespace.
- For cluster wide resources, keep them but add `resourceNames` to specify the exact resource names it can access.

To keep things simple, the modified version only allows the operator to manage PG database clusters in its own namespace. As a result, an application that needs a pg cluster, if running in another namespace, will need to establish db connections to `cnpg-system` namespace, probably with following kustomize structure:

```
.
├── app
│   ├── app-manifest.yaml
│   ├── kustomization.yaml                  # enforce app namespace for all app-specific resources except the cnpg CR
│   └── namespace.yaml                      # app-specific namespace
├── db
│   ├── cloudnative-pg-custom-resource.yaml # cnpg CR without specifying namespace
│   ├── kustomization.yaml                  # enforce `cnpg-system` namespace on cnpg CR
│   └── network-policy.yaml                 # network policy that allows ingress to specific db service from app namespace
└── kustomization.yaml
```
