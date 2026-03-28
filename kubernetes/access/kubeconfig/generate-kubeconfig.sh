#!/bin/sh
set -e

NAMESPACE="access"
LABEL_KEY="access.yuha0.com/kubeconfig-sa"
SERVER="https://kubernetes.default.svc"
CA_CERT="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

# List all service accounts with the kubeconfig annotation set to "true"
SA_LIST=$(kubectl get serviceaccounts -n "$NAMESPACE" \
  -o jsonpath='{range .items[?(@.metadata.annotations.access\.yuha0\.com/kubeconfig=="true")]}{.metadata.name}{"\n"}{end}')

for SA in $SA_LIST; do
  SECRET_NAME="kubeconfig-${SA}"
  echo "Generating kubeconfig for service account: ${SA}"

  # Read the long-lived token from the SA's token secret
  TOKEN_SECRET_NAME="${SA}-token"
  TOKEN=$(kubectl get secret "$TOKEN_SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.token}' | base64 -d)

  # Build kubeconfig
  CA_DATA=$(base64 -w0 < "$CA_CERT")
  KUBECONFIG_DATA=$(cat <<EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: ${CA_DATA}
    server: ${SERVER}
  name: cluster
contexts:
- context:
    cluster: cluster
    namespace: ${NAMESPACE}
    user: ${SA}
  name: ${SA}@cluster
current-context: ${SA}@cluster
users:
- name: ${SA}
  user:
    token: ${TOKEN}
EOF
  )

  # Create or update the secret
  kubectl create secret generic "$SECRET_NAME" \
    -n "$NAMESPACE" \
    --from-literal=kubeconfig="$KUBECONFIG_DATA" \
    --dry-run=client -o yaml | \
    kubectl label --local -f - "${LABEL_KEY}=${SA}" -o yaml | \
    kubectl apply -f -
done

# Cleanup: find kubeconfig secrets for service accounts that no longer have the annotation
EXISTING_SECRETS=$(kubectl get secrets -n "$NAMESPACE" -l "$LABEL_KEY" \
  -o jsonpath='{range .items[*]}{.metadata.labels.access\.yuha0\.com/kubeconfig-sa}{"\n"}{end}')

for SA_NAME in $EXISTING_SECRETS; do
  if ! echo "$SA_LIST" | grep -qx "$SA_NAME"; then
    echo "Deleting orphaned kubeconfig secret: kubeconfig-${SA_NAME}"
    kubectl delete secret "kubeconfig-${SA_NAME}" -n "$NAMESPACE"
  fi
done

echo "Done."
