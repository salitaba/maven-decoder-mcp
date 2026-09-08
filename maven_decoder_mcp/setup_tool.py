"""
Setup helper for the Maven Decoder MCP Server.

Backs the ``maven-decoder-setup`` console script. It downloads the optional
Java decompilers (CFR, Procyon) next to the installed package and reports
what the current environment can do, which is useful when decompilation
silently falls back to ``javap``.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

CFR_URL = "https://www.benf.org/other/cfr/cfr-0.152.jar"
PROCYON_URL = (
    "https://github.com/mstrobel/procyon/releases/download/v0.6.0/"
    "procyon-decompiler-0.6.0.jar"
)

DOWNLOADS: Dict[str, Tuple[str, str]] = {
    "cfr": (CFR_URL, "cfr.jar"),
    "procyon": (PROCYON_URL, "procyon-decompiler.jar"),
}


def decompiler_dir() -> Path:
    """Directory the package looks in for bundled decompiler jars."""
    override = os.environ.get("MAVEN_DECODER_DECOMPILER_DIR", "").strip()
    if override:
        return Path(os.path.expandvars(os.path.expanduser(override)))

    # Prefer a writable location next to the installed package; fall back to
    # the user cache when the install tree is read-only (e.g. system site).
    package_dir = Path(__file__).resolve().parent / "decompilers"
    if os.access(package_dir.parent, os.W_OK):
        return package_dir

    return Path.home() / ".cache" / "maven-decoder-mcp" / "decompilers"


def _download(url: str, target: Path) -> bool:
    """Download a file, writing it atomically. Returns success."""
    target.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".part")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(tmp_fd, "wb") as handle:
            with urllib.request.urlopen(url, timeout=60) as response:
                shutil.copyfileobj(response, handle)
        shutil.move(str(tmp_path), str(target))
        return True
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        tmp_path.unlink(missing_ok=True)
        print(f"  ✗ Failed to download {url}: {exc}")
        return False
    except Exception as exc:  # pragma: no cover - defensive
        tmp_path.unlink(missing_ok=True)
        print(f"  ✗ Unexpected error downloading {url}: {exc}")
        return False


def install_decompilers(force: bool = False) -> int:
    """Download the optional decompiler jars. Returns an exit code."""
    target_dir = decompiler_dir()
    print(f"Installing decompilers into: {target_dir}")

    failures = 0
    for name, (url, filename) in DOWNLOADS.items():
        target = target_dir / filename

        if target.exists() and not force:
            print(f"  ✓ {name} already present ({target.name})")
            continue

        print(f"  → downloading {name} ...")
        if _download(url, target):
            print(f"  ✓ {name} installed")
        else:
            failures += 1

    if failures:
        print(
            f"\n{failures} decompiler(s) could not be installed. "
            "The server still works using javap from the JDK."
        )
        return 1

    print("\n✓ Decompiler setup complete")
    return 0


def _java_version() -> Optional[str]:
    """Return the java version string, or None when java is unavailable."""
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return None

    output = (result.stderr or result.stdout or "").strip().splitlines()
    return output[0] if output else None


def show_status() -> int:
    """Report what this environment supports."""
    from .config import Config
    from .decompiler import JavaDecompiler
    from .maven_decoder_server import get_version

    print(f"maven-decoder-mcp {get_version()}")
    print(f"Python           : {sys.version.split()[0]}")

    java = _java_version()
    print(f"Java             : {java or 'NOT FOUND (decompilation unavailable)'}")

    repo = Config.resolve_maven_repository()
    print(f"Maven repository : {repo}{'' if repo.exists() else '  (missing)'}")

    remote = Config.get_remote_config()
    print(f"Cache directory  : {remote['cache_dir']}")
    print(f"Offline mode     : {remote['offline']}")
    print(f"Auto-download    : {remote['auto_download']}")
    print(f"Remote repos     : {', '.join(remote['remote_repositories'])}")

    available = JavaDecompiler().available_decompilers
    print(f"Decompilers      : {', '.join(available) if available else 'none (javap only)'}")

    if not available:
        print("\nRun 'maven-decoder-setup decompilers' to install CFR and Procyon.")

    return 0


def main() -> int:
    """Entry point for the ``maven-decoder-setup`` console script."""
    parser = argparse.ArgumentParser(
        prog="maven-decoder-setup",
        description="Setup helper for the Maven Decoder MCP server",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=["status", "decompilers"],
        help="'status' reports the environment, 'decompilers' installs CFR and Procyon",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-download decompilers even when they are already installed",
    )

    args = parser.parse_args()

    if args.command == "decompilers":
        return install_decompilers(force=args.force)
    return show_status()


if __name__ == "__main__":
    sys.exit(main())
