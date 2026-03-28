# access

Manages service accounts, roles, and kubeconfig generation for external access to the cluster.

## Structure

- `roles/` - Predefined ClusterRoles shared across service accounts.
  - `access-cluster-viewer` - Read-only access to all cluster resources except secrets.
  - `kubeconfig-generator` - Role used by the kubeconfig generator job.
- `serviceaccounts/` - One subdirectory per service account, each containing the SA definition, token secret, and role bindings.
- `kubeconfig/` - ArgoCD PostSync hook job that generates kubeconfig files for service accounts.

## Adding a new service account

1. Create a new directory under `serviceaccounts/<name>/`.
2. Define the ServiceAccount in `serviceaccount.yaml`:
   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: <name>
   ```
3. Define a ClusterRoleBinding in `clusterrolebinding.yaml` to bind the SA to a role (e.g. `access-cluster-viewer`).
4. Add a `kustomization.yaml` referencing the above files.
5. Add the new directory to `serviceaccounts/kustomization.yaml`.
6. (Optional) If the service account needs a kubeconfig for external cluster access, add the annotation and a token secret to `serviceaccount.yaml`:
   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: <name>
     annotations:
       access.yuha0.com/kubeconfig: "true"
   ---
   apiVersion: v1
   kind: Secret
   metadata:
     name: <name>-token
     annotations:
       kubernetes.io/service-account.name: <name>
   type: kubernetes.io/service-account-token
   ```
   The token secret provides a long-lived token. The kubeconfig generator job will automatically pick it up on the next ArgoCD sync and create a `kubeconfig-<name>` secret in the `access` namespace.

## Kubeconfig generation

The `kubeconfig/` job runs as an ArgoCD PostSync hook. It:

1. Finds all service accounts annotated with `access.yuha0.com/kubeconfig: "true"`.
2. Reads the long-lived token from the `<sa-name>-token` secret.
3. Generates a kubeconfig and stores it in a secret named `kubeconfig-<sa-name>`.
4. Cleans up kubeconfig secrets for service accounts that no longer have the annotation.
