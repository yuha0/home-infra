# cloudnative-pg

Upstream manifests/helm chart create clusterroles with cluster wide permissions that are probably too wide(e.g.: all verbs on secrets in all namespaces). I sync a copy of upstream release manifest in the `base` directory, leverage kustomize patches to delete the rbac parts, and add custom role/clusterrole with more restricted access in `rbac.yaml`. Specifically:

- The clusterrole only grants access to operator's own CRDs, necessary admission webhooks, and read-only access to certain non-sensitive (e.g. namespace names).
- The role grants the opeartor wider access to namespaced resources, but only in its own namespace.

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
