#!/usr/bin/env python3
"""
pre-commit hook: auto-seal Kubernetes secrets with kubeseal.

The pre-commit framework pre-filters staged files via the `files` / `exclude`
/ `types` rules in .pre-commit-config.yaml, then passes the matching paths as
argv arguments.  This script seals each one and exits 1 so the framework aborts
the current commit; the developer runs `git commit` again and this time only
the *-sealed.yaml files are staged.

Configuration
─────────────
  CERT_PATH     – path to the Sealed-Secrets public-key certificate
  KUBESEAL_ARGS – extra kubeseal flags (--namespace, --controller-name, etc.)
"""

import subprocess
import sys
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

CERT_PATH = "sealed-secrets-cert.pem"  # path to kubeseal public cert
KUBESEAL_ARGS = [                       # extend with --namespace etc. as needed
    "--format=yaml",
    f"--cert={CERT_PATH}",
]

# ─────────────────────────────────────────────────────────────────────────────


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, raise on non-zero exit."""
    return subprocess.run(cmd, check=True, **kwargs)


def sealed_path(original: Path) -> Path:
    """
    Given  secrets/my-secret.yaml
    Return secrets/my-secret-sealed.yaml
    """
    return original.with_stem(original.stem + "-sealed")


def seal_file(original: Path) -> bool:
    """
    Unstage, seal, re-stage, and delete the original file.
    Returns True on success, False on failure.
    """
    sealed = sealed_path(original)
    print(f"  [kubeseal] {original} → {sealed}")

    # 1. Unstage the original so it won't be committed as plain-text.
    run(["git", "reset", "HEAD", str(original)])

    # 2. Run kubeseal.
    kubeseal_cmd = ["kubeseal"] + KUBESEAL_ARGS
    with original.open("rb") as infile, sealed.open("wb") as outfile:
        result = subprocess.run(
            kubeseal_cmd,
            stdin=infile,
            stdout=outfile,
            stderr=subprocess.PIPE,
            check=False,
        )

    if result.returncode != 0:
        print(
            f"ERROR: kubeseal failed for {original}:\n"
            f"{result.stderr.decode().strip()}",
            file=sys.stderr,
        )
        # Re-stage the original so the developer doesn't lose their work.
        run(["git", "add", str(original)])
        return False

    # 3. Stage the sealed file.
    run(["git", "add", str(sealed)])

    # 4. Remove the original plain-text file from disk.
    original.unlink()
    print(f"  [kubeseal] deleted original: {original}")
    return True


def main(argv: list[str]) -> int:
    # The pre-commit framework passes staged file paths as argv[1:].
    files = [Path(p) for p in argv[1:]]

    if not files:
        return 0

    print(f"pre-commit [kubeseal]: sealing {len(files)} file(s)…")

    failed = False
    for f in files:
        if not seal_file(f):
            failed = True

    if failed:
        return 1

    print("pre-commit [kubeseal]: done — re-run 'git commit' to commit sealed files.")
    # Exit 1 to abort the current commit; the developer re-runs git commit
    # and only the *-sealed.yaml files will be staged.
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
