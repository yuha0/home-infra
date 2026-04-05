"""
Upgrade helm chart version with newer values.yaml while retaining local modifications.

Flow:
  1. Read helm-lock.json to determine the current chart version and repo.
  2. Refresh the helm repo and resolve the target version (latest if unspecified).
  3. If the target differs from the current version, download both the old and new
     upstream default values.yaml from git.
  4. Run `git merge-file` to 3-way merge the upstream changes into the local file:
     current = user's customized values.yaml, base = old upstream, other = new upstream.
     Conflict markers are inserted where local edits clash with upstream changes.
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
        "gitValuesPath": "https://raw.githubusercontent.com/cloudnative-pg/charts/refs/tags/{gitTag}/charts/cloudnative-pg/values.yaml",
        "gitTagFormat": "cloudnative-pg-v{version}",
        "version": "0.24.0"
    },
    "releaseName": "cnpg",
    "valuesFile": "./values.yaml",
    "extraTemplateArgs": []
}

```

Run this script from that directory to patch the values.yaml and generate manifest
from newer chart version.
"""
import argparse
import json
import subprocess
import logging
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


def seaweedtag(chart_version):
    match = re.match(r"(\d+)\.(\d+)\.0", chart_version)
    tag = f"{match.group(1)}.{match.group(2)}"
    logging.warning("Special handling for seaweedfs due to values.yaml being tracked by app version tag and not chart version tag: extracted app version %s from chart version %s", tag, chart_version)
    return tag


def check_values(chart_info, values_file):
    if os.path.isfile(values_file):
        return
    tag = chart_info["gitTagFormat"].format(version=chart_info["version"])
    if chart_info["name"] == "seaweedfs":
        tag = seaweedtag(chart_info["version"])
    url = chart_info["gitValuesPath"].format(gitTag=tag)
    get_remote_file(url, values_file)


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


def get_remote_file(url, path):
    with urllib.request.urlopen(url) as remote:
        content = remote.read()
    with open(path, "wb") as f:
        f.write(content)


def merge_values(chart_info, newv, values_file, workdir="/tmp"):
    """3-way merge: upstream old → upstream new, applied to the user's values_file."""
    old_tag = chart_info["gitTagFormat"].format(version=chart_info["version"])
    if chart_info["name"] == "seaweedfs":
        old_tag = seaweedtag(chart_info["version"])
    old_url = chart_info["gitValuesPath"].format(gitTag=old_tag)
    old_file = os.path.join(workdir, f"{chart_info['version']}-values.yaml")
    get_remote_file(old_url, old_file)

    new_tag = chart_info["gitTagFormat"].format(version=newv)
    if chart_info["name"] == "seaweedfs":
        new_tag = seaweedtag(newv)
    new_url = chart_info["gitValuesPath"].format(gitTag=new_tag)
    new_file = os.path.join(workdir, f"{newv}-values.yaml")
    get_remote_file(new_url, new_file)

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
    elif p.returncode > 0:
        logging.error(
            "Merged with %d conflict(s) — resolve manually in %s then re-run",
            p.returncode, values_file,
        )
        sys.exit(1)
    else:
        logging.error("Merge failed: %s", p.stderr.decode())
        sys.exit(1)


def helm_template(args, output):
    generated = run_helm(args)
    with open(output, "w") as f:
        f.write(generated)
    logging.info("Rendered manifests from template at %s", output)


def main():
    args = get_config()
    lock = get_lock(args.lock)
    new_version = False

    check_values(lock["chart"], args.values)

    target_version = helm_repo_refresh(
        lock["repo"]["name"], lock["repo"]["url"], lock["chart"]["name"], args.target
    )
    if lock["chart"]["version"] != target_version:
        new_version = True
        logging.info(
            "Refreshed repo %s and located target version %s",
            lock["repo"]["name"],
            target_version,
        )
        merge_values(lock["chart"], target_version, args.values, workdir=args.workdir)
    else:
        logging.info("Chart's current version and target version are the same")
    helm_template_args = [
        "template",
        f"-f={args.values}",
        f"--version={target_version}",
        lock["releaseName"],
        f"{lock['repo']['name']}/{lock['chart']['name']}",
    ]
    helm_template_args.extend(lock["extraTemplateArgs"])
    helm_template(
        helm_template_args,
        os.path.join(os.path.dirname(args.values), "../generated.yaml"),
    )

    if new_version:
        lock["chart"]["version"] = target_version
        with open(args.lock, "w") as f:
            json.dump(lock, f, indent=2, sort_keys=False)
            f.write("\n")
        logging.info("lock version updated")


if __name__ == "__main__":
    main()
