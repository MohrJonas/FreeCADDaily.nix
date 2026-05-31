from requests import get
from json import dumps, loads
from sys import exit, stdout, stderr
from pathlib import Path
from os import environ
from subprocess import run, PIPE

branch_name = "main"
repo_owner = "freecad"
repo_name = "freecad"

def main():
    print("Loading repo info")
    repo_info = loads(Path("repo.json").read_text())
    
    last_commit_hash = repo_info["commitHash"]
    print(f"Last commit hash was {last_commit_hash}")

    request_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches/{branch_name}"
    response = get(request_url)
    
    if(not response.ok):
        print(f"Getting branch information failed with status code {response.status_code}: {response.text}")
        exit(1)
    
    response_body = response.json()

    commit_hash = response_body["commit"]["sha"]
    print(f"Lastest commit hash is {commit_hash}")

    if(commit_hash == last_commit_hash):
        print("Reposity has not been updated since last run, doing nothing")
        exit(0)

    print("Repository has been updated since last run, proceeding")

    archive_url = f"https://github.com/{repo_owner}/{repo_name}/archive/{commit_hash}.tar.gz"
    print(f"Fetching hash of archive {archive_url}")

    res = run(["nix-prefetch-url", "--type", "sha256", archive_url], stdout=PIPE, stderr=stderr)
    res.check_returncode()
    
    base32_hash = res.stdout.decode().strip()
    print(f"Base32 hash is {base32_hash}")

    res = run(["nix", "hash", "convert", "--hash-algo", "sha256", "--to", "sri", base32_hash], stdout=PIPE, stderr=stderr)
    res.check_returncode()

    sri_hash = res.stdout.decode().strip()
    print(f"SRI-hash is {sri_hash}")

    file_contents = {
        "commitHash": commit_hash,
        "sriHash": sri_hash,
        "version": commit_hash[:7]
    }
    file_text = dumps(file_contents, indent=4)
    print(f"New file text is\n{file_text}")

    Path("repo.json").write_text(file_text)
    print("Wrote new contents to file")

    run(["git", "config", "user.name", "daily-update-run"], stdout=stdout, stderr=stderr).check_returncode()
    run(["git", "config", "user.email", "git@al1as.me"], stdout=stdout, stderr=stderr).check_returncode()

    run(["git", "add", "repo.json"], stdout=stdout, stderr=stderr).check_returncode()
    run(["git", "commit", "-m", f"Automatic update {last_commit_hash} -> {commit_hash}"], stdout=stdout, stderr=stderr).check_returncode()
    run(["git", "remote", "set-url", "origin", f"https://mohrjonas:{environ.get("GITHUB_TOKEN")}@github.com/mohrjonas/FreeCADDaily.nix.git"], stdout=stdout, stderr=stderr).check_returncode()
    run(["git", "push", "origin", "main"], stdout=stdout, stderr=stderr).check_returncode()

if __name__ == "__main__":
    main()