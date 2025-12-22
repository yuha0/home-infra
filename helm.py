"""
Upgrade helm chart version with newer values.yaml while retaining modification in values.yaml.

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

Run this script from that directory to patch the values.yaml and generate manifest from newer chart version. Will migrate most of helm generated manifests to be managed in this way.
"""
import argparse
import json
import subprocess
import logging
import urllib.request
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


def check_values(chart_info, values_file):
    if os.path.isfile(values_file):
        return
    tag = chart_info["gitTagFormat"].format(version=chart_info["version"])
    if chart_info["name"] == "seaweedfs":
        match = re.match(r"(\d+)\.\d+\.(\d)(\d+)", chart_info["version"])
        tag = f"{match.group(2)}.{match.group(3)}"
        logging.warning("Special handling for seaweedfs due to values.yaml being tracked by app version tag and not chart version tag: extracted app version %s from chart version %s", tag, chart_info["version"])
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


def gen_values_diff(chart_info, newv, workdir="/tmp", diff_file="values.diff"):
    old_tag = chart_info["gitTagFormat"].format(version=chart_info["version"])
    old_url = chart_info["gitValuesPath"].format(gitTag=old_tag)
    old_file = os.path.join(workdir, f"{chart_info['version']}-values.yaml")
    get_remote_file(old_url, old_file)

    new_tag = chart_info["gitTagFormat"].format(version=newv)
    new_url = chart_info["gitValuesPath"].format(gitTag=new_tag)
    new_file = os.path.join(workdir, f"{newv}-values.yaml")
    get_remote_file(new_url, new_file)

    diff_path = os.path.join(workdir, diff_file)
    with open(diff_path, "w") as diff:
        p = subprocess.run(["diff", old_file, new_file], stdout=diff)
    if p.returncode not in (0, 1):
        logging.error(
            "Failed to generate diff between %s and %s: %s",
            chart_info["version"],
            newv,
            p.stderr.decode(),
        )
        sys.exit(1)
    elif p.returncode == 1:
        logging.info(
            "diff between %s and %s generated in %s",
            chart_info["version"],
            newv,
            diff_path,
        )
        return diff_path
    else:
        logging.info("no diff between %s and %s", chart_info["version"], newv)


def patch(values_file, patch_file):
    p = subprocess.run(["patch", values_file, patch_file], capture_output=True)
    if p.returncode != 0:
        logging.error(p.stderr.decode())
    else:
        logging.info(p.stdout.decode())


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
        diff_path = gen_values_diff(lock["chart"], target_version, workdir=args.workdir)
        if diff_path:
            patch(args.values, diff_path)
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
