#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

for c in curl jq kustomize; do
    command -v "$c" >/dev/null || { echo "missing dependency: $c" >&2; exit 1; }
done

token() {
    curl -fsS "https://ghcr.io/token?scope=repository:$1:pull&service=ghcr.io" | jq -r .token
}

# Resolve to the multi-arch index digest; pinning a per-arch manifest would make
# the image unpullable on half the cluster.
digest() {
    curl -sI -H "Authorization: Bearer $2" \
        -H 'Accept: application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json' \
        "https://ghcr.io/v2/$1/manifests/$3" \
        | tr -d '\r' | awk 'tolower($1) == "docker-content-digest:" { print $2 }'
}

# The registry offers no digest-to-tag lookup and the GitHub packages API needs
# a token, so walk the commit tags until one matches.
commit_for_digest() {
    local img=$1 tok=$2 want=$3 t
    for t in $(curl -fsS -H "Authorization: Bearer $tok" \
        "https://ghcr.io/v2/$img/tags/list?n=1000" | jq -r '.tags[]' | grep -Ex '[0-9a-f]{40}'); do
        if [[ "$(digest "$img" "$tok" "$t")" == "$want" ]]; then
            printf '%s' "$t"
            return 0
        fi
    done
    return 1
}

resolve() {
    local img=$1 prefer=${2-} tok tag dg
    tok=$(token "$img")
    if [[ -n $prefer ]]; then
        dg=$(digest "$img" "$tok" "$prefer")
        if [[ -n $dg ]]; then
            printf '%s %s' "$prefer" "$dg"
            return 0
        fi
        echo "  $prefer has no image yet, using :latest" >&2
    fi
    dg=$(digest "$img" "$tok" latest)
    [[ -n $dg ]] || { echo "could not resolve $img:latest" >&2; return 1; }
    tag=$(commit_for_digest "$img" "$tok" "$dg") \
        || { echo "no commit tag matches $img@$dg" >&2; return 1; }
    printf '%s %s' "$tag" "$dg"
}

current_tag() {
    awk -v n="$1" '$0 ~ "name: "n"$" { f = 1 } f && /newTag:/ { print $2; exit }' kustomization.yaml
}

# Ente rebuilds the server image monthly from whichever commit their own
# production is serving, so /ping names the newest commit worth pinning.
prod=$(curl -fsS https://api.ente.com/ping | jq -r .id)
[[ $prod =~ ^[0-9a-f]{40}$ ]] || { echo "unexpected /ping id: $prod" >&2; exit 1; }
echo "ente production museum: $prod"

old_server=$(current_tag museum)
old_web=$(current_tag ente-web)

echo "resolving ghcr.io/ente/server ..."
read -r server_tag server_digest <<<"$(resolve ente/server "$prod")"
echo "resolving ghcr.io/ente/web ..."
read -r web_tag web_digest <<<"$(resolve ente/web)"
[[ -n $server_digest && -n $web_digest ]] || { echo "resolution failed" >&2; exit 1; }

kustomize edit set image "museum=ghcr.io/ente/server:${server_tag}@${server_digest}"
kustomize edit set image "ente-web=ghcr.io/ente/web:${web_tag}@${web_digest}"

changed=0
for pair in "server:$old_server:$server_tag" "web:$old_web:$web_tag"; do
    IFS=: read -r name old new <<<"$pair"
    if [[ $old == "$new" ]]; then
        echo "$name unchanged ($new)"
    else
        changed=1
        echo "$name $old -> $new"
        echo "  https://github.com/ente/ente/compare/${old}...${new}"
    fi
done

[[ $changed -eq 1 ]] || exit 0
kustomize build . >/dev/null
echo "kustomize build ok; review and commit kustomization.yaml"
