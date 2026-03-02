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

CERT_PATH = "../pub.pem"  # path to kubeseal public cert
KUBESEAL_ARGS = [                       # extend with --namespace etc. as needed
    "--format=yaml",
    f"--cert={CERT_PATH}",
]

# ─────────────────────────────────────────────────────────────────────────────


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, raise on non-zero exit."""
    return subprocess.run(cmd, check=True, **kwargs)


def is_already_sealed(path: Path) -> bool:
    """Return True if the file stem already ends with '-sealed'."""
    return path.stem.endswith("-sealed")


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
    # Belt-and-suspenders: skip if already sealed even if yaml filter missed it.
    if is_already_sealed(original):
        print(f"  [kubeseal] skipping (already sealed): {original}")
        return True

    sealed = sealed_path(original)
    print(f"  [kubeseal] {original} → {sealed}")

    # 1. Unstage the original so it won't be committed as plain-text.
    run(["git", "reset", "HEAD", str(original)])

    # 2. Run kubeseal, writing output to a temp bytes buffer first so we only
    #    write the sealed file to disk once we know kubeseal succeeded.
    kubeseal_cmd = ["kubeseal"] + KUBESEAL_ARGS
    with original.open("rb") as infile:
        result = subprocess.run(
            kubeseal_cmd,
            stdin=infile,
            capture_output=True,  # collect stdout + stderr in memory
            check=False,
        )

    if result.returncode != 0:
        print(
            f"  ERROR: kubeseal failed for {original}:\n"
            f"  {result.stderr.decode().strip()}",
            file=sys.stderr,
        )
        # Re-stage the original so the developer doesn't lose their work.
        run(["git", "add", str(original)])
        return False

    # 3. Write the sealed output to disk (only now that kubeseal succeeded).
    sealed.write_bytes(result.stdout)

    # 4. Stage the sealed file.
    run(["git", "add", str(sealed)])

    # 5. Remove the original plain-text file from disk.
    original.unlink()
    print(f"  [kubeseal] deleted original: {original}")
    return True


def main(argv: list[str]) -> int:
    # The pre-commit framework passes staged file paths as argv[1:].
    # Filter out any already-sealed files up-front so we report an accurate count.
    all_files  = [Path(p) for p in argv[1:]]
    to_seal    = [f for f in all_files if not is_already_sealed(f)]
    to_skip    = [f for f in all_files if is_already_sealed(f)]

    if to_skip:
        for f in to_skip:
            print(f"  [kubeseal] skipping (already sealed): {f}")

    if not to_seal:
        # Nothing to do — let the commit proceed.
        return 0

    print(f"pre-commit [kubeseal]: sealing {len(to_seal)} file(s)…")

    sealed_ok: list[Path] = []
    failed:    list[Path] = []

    for f in to_seal:
        if seal_file(f):
            sealed_ok.append(f)
        else:
            failed.append(f)

    # Report results.
    for f in sealed_ok:
        print(f"  [kubeseal] ✓ sealed: {sealed_path(f)}")

    if failed:
        print(
            f"\npre-commit [kubeseal]: {len(failed)} file(s) failed to seal — "
            "originals have been re-staged.",
            file=sys.stderr,
        )
        return 1

    print(
        f"pre-commit [kubeseal]: {len(sealed_ok)} file(s) sealed. "
        "Re-run 'git commit' to commit the sealed files."
    )
    # Exit 1 to abort the current commit; the developer re-runs git commit
    # and only the *-sealed.yaml files will be staged.
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
