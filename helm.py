"""
Upgrade helm chart version with newer values.yaml while retaining local modifications.

Flow:
  1. Read helm-lock.json to determine the current chart version and repo.
  2. Refresh the helm repo and resolve the target version (latest if unspecified).
  3. If the target differs from the current version, fetch both the old and new
     upstream default values.yaml from the packaged charts (`helm show values`),
     which prints the raw authored file — comments included — as shipped by the
     chart author.
  4. Run `git merge-file` to 3-way merge the upstream changes into the local file:
     current = user's customized values.yaml, base = old upstream, other = new upstream.
     Conflict markers are inserted where local edits clash with upstream changes.
     On conflict the lock is bumped to the target version anyway (the file has
     already been rebased onto it) and the script exits so the user can resolve
     the markers. A re-run then finds versions matching, skips the merge, and
     renders. A startup guard refuses to run while conflict markers remain.
  6. Run `helm template` against the (now patched) values.yaml to render manifests.
  7. Update helm-lock.json with the new version.

For each helm application folder, create a subfolder and place a `helm-lock.json` in it:

```
{
    "repo": {
        "name": "cnpg",
        "url": "https://cloudnative-pg.github.io/charts"
    },
    "chart": {
        "name": "cloudnative-pg",
        "version": "0.24.0"
    },
    "releaseName": "cnpg",
    "valuesFile": "./values.yaml",
    "extraTemplateArgs": []
}

```

Run this script from that directory to patch the values.yaml and generate manifest
from newer chart version.

OCI repos are supported and detected by URL scheme (`"url": "oci://docker.io/envoyproxy"`).
For OCI charts:
  - Versions are listed via the OCI Distribution API (`/v2/<repo>/tags/list`) with
    anonymous bearer-token auth, since `helm search repo` cannot see OCI registries.
  - `repo.name` is unused (no `helm repo add`); the chart ref is `<repo.url>/<chart.name>`.
"""
import argparse
import json
import subprocess
import logging
import urllib.error
import urllib.parse
import urllib.request
import sys
import os
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%y%m%d %H:%M:%S",
)


def get_config():
    # cli args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--values",
        type=str,
        default="./values.yaml",
        help="values.yaml file to patch",
    )
    parser.add_argument(
        "-l",
        "--lock",
        type=str,
        default="./helm-lock.json",
        help="Path to the lock file. Attempt to open ./helm-lock.json if not specified",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        default="",
        help="Target helm chart version. Attempt to discover the latest if not specified",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        type=str,
        default="/tmp",
        help="Temporary workdir for downloading values.yaml files, generating diff for patching...etc",
    )
    return parser.parse_args()


def get_lock(lockfile):
    with open(lockfile, "r") as f:
        lock = json.load(f)
    return lock


def is_oci(repo_url):
    return repo_url.startswith("oci://")


def chart_ref(repo, chart_name):
    """Chart reference for helm template/show: repo alias for classic repos,
    full oci:// URL for OCI registries (which have no repo alias)."""
    if is_oci(repo["url"]):
        return f"{repo['url'].rstrip('/')}/{chart_name}"
    return f"{repo['name']}/{chart_name}"


def check_conflict_markers(values_file):
    """Abort if values_file still contains unresolved merge conflict markers.

    A previous run may have left conflicts in place after bumping the lock (see
    merge_values). Refuse to proceed until they are resolved, rather than feeding
    a broken file to `helm template` and emitting a confusing YAML parse error.
    """
    if not os.path.isfile(values_file):
        return
    with open(values_file, "r") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.rstrip("\n")
            if (
                stripped.startswith("<<<<<<<")
                or stripped.startswith(">>>>>>>")
                or stripped == "======="
            ):
                logging.error(
                    "Unresolved conflict marker at %s:%d — resolve existing "
                    "conflicts before re-running",
                    values_file,
                    lineno,
                )
                sys.exit(1)


def check_values(repo, chart_info, values_file):
    if os.path.isfile(values_file):
        return
    fetch_default_values(repo, chart_info, chart_info["version"], values_file)


def run_helm(args, output=False):
    cmd = ["helm", *args]
    cp = subprocess.run(cmd, capture_output=True, check=True)
    result = cp.stdout.decode()
    if output:
        logging.info(result)
    return result


def helm_repo_refresh(repo_name, repo_url, chart_name, version):
    repo_exists = False
    for l in run_helm(["repo", "list"]).split("\n")[1:]:
        if not l:
            continue
        name, url = l.split()
        if name == repo_name and url.strip("/") == repo_url.strip("/"):
            repo_exists = True
            logging.info(
                "repo %s at %s already exists, skip adding", repo_name, repo_url
            )
    if not repo_exists:
        logging.info("repo %s at %s does not exist, adding...", repo_name, repo_url)
        run_helm(["repo", "add", repo_name, repo_url], True)
    run_helm(["repo", "update", repo_name], True)
    result = run_helm(["search", "repo", f"{repo_name}/{chart_name}", "--versions"])
    versions = []
    for l in result.split("\n")[1:]:
        if l:
            versions.append(l.split()[1])
    def _version_sort(v):
        version = re.search('\d+\.[\d\.]+\d$', v).group()
        return list(map(int, version.split('.')))
    versions.sort(key=_version_sort)
    if version in versions:
        return version
    else:
        latest = versions[-1]
        logging.info(
            "Target version not specified or not found, use latest version %s", latest
        )
        return latest


def oci_registry_endpoint(repo_url, chart_name):
    """Split oci://host/path + chart into (registry host, repository path)."""
    ref = repo_url[len("oci://"):].strip("/") + "/" + chart_name
    host, _, repository = ref.partition("/")
    # docker.io is a pull alias, not a real registry endpoint (it redirects to
    # www.docker.com); the distribution API lives at registry-1.docker.io.
    if host in ("docker.io", "index.docker.io"):
        host = "registry-1.docker.io"
    return host, repository


def oci_auth_token(challenge, repository):
    """Fetch an anonymous pull token per the WWW-Authenticate bearer challenge."""
    params = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
    if "realm" not in params:
        return None
    query = {"scope": f"repository:{repository}:pull"}
    if "service" in params:
        query["service"] = params["service"]
    if "scope" in params:
        query["scope"] = params["scope"]
    url = f"{params['realm']}?{urllib.parse.urlencode(query)}"
    with urllib.request.urlopen(url) as resp:
        body = json.load(resp)
    return body.get("token") or body.get("access_token")


def oci_list_tags(repo_url, chart_name):
    """List all tags of an OCI repository via the distribution API, following
    Link-header pagination and the anonymous bearer-token auth flow."""
    host, repository = oci_registry_endpoint(repo_url, chart_name)
    url = f"https://{host}/v2/{repository}/tags/list"
    token = None
    tags = []
    while url:
        req = urllib.request.Request(url)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            if e.code == 401 and not token:
                token = oci_auth_token(e.headers.get("WWW-Authenticate", ""), repository)
                if token:
                    continue
            logging.error("Failed to list tags at %s: %s", url, e)
            sys.exit(1)
        with resp:
            tags.extend(json.load(resp).get("tags") or [])
            link = resp.headers.get("Link", "")
        m = re.search(r"<([^>]+)>", link)
        url = urllib.parse.urljoin(url, m.group(1)) if m else None
    return tags


def oci_resolve_version(repo_url, chart_name, version):
    """OCI counterpart of helm_repo_refresh: chart versions are registry tags.
    Latest is picked from stable semver tags only (mirroring `helm search repo`,
    which hides prereleases), but an explicitly pinned prerelease tag is honored."""
    tags = oci_list_tags(repo_url, chart_name)
    if version in tags:
        return version
    versions = [t for t in tags if re.fullmatch(r"v?\d+\.\d+\.\d+", t)]
    if not versions:
        logging.error(
            "No semver tags found for %s in %s (tags: %s)", chart_name, repo_url, tags
        )
        sys.exit(1)
    # Some registries publish both "1.8.3" and "v1.8.3" for the same chart
    # version; sort the plain tag after its v-prefixed twin so it wins, matching
    # what helm itself resolves (the OCI tag equals the Chart.yaml version).
    versions.sort(
        key=lambda v: (list(map(int, v.lstrip("v").split("."))), not v.startswith("v"))
    )
    latest = versions[-1]
    logging.info(
        "Target version not specified or not found, use latest version %s", latest
    )
    return latest


def fetch_default_values(repo, chart_info, version, path):
    """Fetch the upstream default values.yaml for a given chart version from the
    packaged chart itself. `helm show values` prints the raw authored file from
    the chart archive (comments and all), so it carries the author's intentional
    changes just like the file in git — and it is what helm actually installs,
    which can differ from git (e.g. envoy gateway packages a rendered
    values.tmpl.yaml). For classic repos this requires the repo to be
    added/refreshed first (main() resolves the target version before calling
    this, which does exactly that)."""
    content = run_helm(
        ["show", "values", chart_ref(repo, chart_info["name"]), f"--version={version}"]
    )
    with open(path, "w") as f:
        f.write(content)


def merge_values(repo, chart_info, newv, values_file, workdir="/tmp"):
    """3-way merge: upstream old → upstream new, applied to the user's values_file."""
    old_file = os.path.join(workdir, f"{chart_info['version']}-values.yaml")
    fetch_default_values(repo, chart_info, chart_info["version"], old_file)

    new_file = os.path.join(workdir, f"{newv}-values.yaml")
    fetch_default_values(repo, chart_info, newv, new_file)

    # git merge-file modifies values_file in-place:
    #   current = values_file (user's customized version)
    #   base    = old_file    (old upstream defaults)
    #   other   = new_file    (new upstream defaults)
    p = subprocess.run(
        ["git", "merge-file", "-L", "ours", "-L", "base", "-L", "theirs",
         values_file, old_file, new_file],
        capture_output=True,
    )
    if p.returncode == 0:
        logging.info("Merged upstream %s → %s cleanly", chart_info["version"], newv)
        return False
    elif p.returncode > 0:
        logging.error(
            "Merged with %d conflict(s) — resolve manually in %s then re-run",
            p.returncode, values_file,
        )
        return True
    else:
        logging.error("Merge failed: %s", p.stderr.decode())
        sys.exit(1)


def write_lock(lockfile, lock, version):
    lock["chart"]["version"] = version
    with open(lockfile, "w") as f:
        json.dump(lock, f, indent=2, sort_keys=False)
        f.write("\n")
    logging.info("lock version updated to %s", version)


def helm_template(args, output):
    generated = run_helm(args)
    with open(output, "w") as f:
        f.write(generated)
    logging.info("Rendered manifests from template at %s", output)


def main():
    args = get_config()
    lock = get_lock(args.lock)
    new_version = False

    if is_oci(lock["repo"]["url"]):
        target_version = oci_resolve_version(
            lock["repo"]["url"], lock["chart"]["name"], args.target
        )
    else:
        # also registers/refreshes the repo, which fetch_default_values needs
        target_version = helm_repo_refresh(
            lock["repo"]["name"], lock["repo"]["url"], lock["chart"]["name"], args.target
        )
    check_values(lock["repo"], lock["chart"], args.values)
    check_conflict_markers(args.values)
    if lock["chart"]["version"] != target_version:
        new_version = True
        logging.info(
            "Refreshed repo %s and located target version %s",
            lock["repo"]["name"],
            target_version,
        )
        conflict = merge_values(
            lock["repo"], lock["chart"], target_version, args.values, workdir=args.workdir
        )
        if conflict:
            # git merge-file has already rebased values.yaml onto the target
            # version (conflict markers and all). Bump the lock now so that a
            # re-run — after the user resolves the markers — sees the versions
            # match, skips the merge entirely, and proceeds straight to render.
            # Without this, the next run would re-diff against the stale base
            # and re-conflict on the same lines.
            write_lock(args.lock, lock, target_version)
            sys.exit(1)
    else:
        logging.info("Chart's current version and target version are the same")
    helm_template_args = [
        "template",
        f"-f={args.values}",
        f"--version={target_version}",
        lock["releaseName"],
        chart_ref(lock["repo"], lock["chart"]["name"]),
    ]
    helm_template_args.extend(lock["extraTemplateArgs"])
    helm_template(
        helm_template_args,
        os.path.join(os.path.dirname(args.values), "../generated.yaml"),
    )

    if new_version:
        write_lock(args.lock, lock, target_version)


if __name__ == "__main__":
    main()
