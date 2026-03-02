#!/usr/bin/env python3
"""
pre-commit hook: auto-seal Kubernetes secrets with kubeseal.

The pre-commit framework passes every staged YAML file in secrets/ that does
NOT already end with '-sealed' as argv arguments (filtered by .pre-commit-config.yaml).

For each file this hook will:
  1. Remove the original from the git index  (git rm --cached)
  2. Run kubeseal to produce <name>-sealed.<ext>
  3. Stage the sealed file                   (git add)
  4. Delete the original from disk

Exit behaviour
──────────────
  All files sealed  →  exit 0  (commit proceeds immediately with sealed files)
  Any file failed   →  exit 1  (commit aborted; originals are re-staged so
                                 nothing is lost)

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
    secrets/mysecret.yaml  →  secrets/mysecret-sealed.yaml
    secrets/mysecret.yml   →  secrets/mysecret-sealed.yml
    """
    return original.with_stem(original.stem + "-sealed")


def seal_file(original: Path) -> bool:
    """
    Remove original from index, seal it, stage the sealed file, delete original.
    Returns True on success, False on kubeseal failure (original is re-staged).
    """
    # Belt-and-suspenders guard — skip anything that somehow slipped past the
    # YAML exclude pattern.
    if is_already_sealed(original):
        print(f"  [kubeseal] skipping (already sealed): {original}")
        return True

    sealed = sealed_path(original)
    print(f"  [kubeseal] sealing: {original} → {sealed}")

    # 1. Remove the original from the git index so it is NOT committed as
    #    plain-text. git rm --cached works for both new (untracked) and
    #    previously-committed files, unlike git reset HEAD which can misbehave
    #    on brand-new staged files.
    run(["git", "rm", "--cached", str(original)])

    # 2. Run kubeseal, collecting all output in memory so we never write a
    #    partial/empty sealed file to disk if kubeseal fails.
    kubeseal_cmd = ["kubeseal"] + KUBESEAL_ARGS
    with original.open("rb") as infile:
        result = subprocess.run(
            kubeseal_cmd,
            stdin=infile,
            capture_output=True,
            check=False,
        )

    if result.returncode != 0:
        print(
            f"  ERROR: kubeseal failed for {original}:\n"
            f"  {result.stderr.decode().strip()}",
            file=sys.stderr,
        )
        # Re-stage the original so nothing is lost and the developer can retry.
        run(["git", "add", str(original)])
        return False

    # 3. Write sealed output to disk only after a confirmed kubeseal success.
    sealed.write_bytes(result.stdout)

    # 4. Stage the sealed file so it is included in the commit.
    run(["git", "add", str(sealed)])

    # 5. Delete the original plain-text file from disk.
    original.unlink()
    print(f"  [kubeseal] ✓ {sealed}  (original deleted)")
    return True


def main(argv: list[str]) -> int:
    # pre-commit passes staged matching file paths as argv[1:].
    # Split into files to process vs files to skip (safety net for the exclude
    # pattern in .pre-commit-config.yaml).
    all_files = [Path(p) for p in argv[1:]]
    to_seal   = [f for f in all_files if not is_already_sealed(f)]
    to_skip   = [f for f in all_files if     is_already_sealed(f)]

    for f in to_skip:
        print(f"  [kubeseal] skipping (already sealed): {f}")

    if not to_seal:
        return 0  # nothing to do — let the commit proceed

    print(f"pre-commit [kubeseal]: processing {len(to_seal)} file(s) in secrets/")

    sealed_ok: list[Path] = []
    failed:    list[Path] = []

    # Process every file regardless of individual failures so the developer
    # gets a complete picture of what succeeded and what needs attention.
    for f in to_seal:
        if seal_file(f):
            sealed_ok.append(f)
        else:
            failed.append(f)

    if failed:
        print(
            f"\npre-commit [kubeseal]: {len(failed)} file(s) failed — "
            f"originals have been re-staged. Fix the errors above and re-commit.",
            file=sys.stderr,
        )
        return 1  # abort commit; originals are safely re-staged

    # All files sealed successfully.  Exit 0 so the commit proceeds immediately
    # with the sealed files in the index.  No need to re-run git commit.
    print(
        f"pre-commit [kubeseal]: {len(sealed_ok)} file(s) sealed and staged. "
        "Commit will include the sealed files."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
