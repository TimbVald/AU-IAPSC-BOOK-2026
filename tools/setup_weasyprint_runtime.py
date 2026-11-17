"""Install MSYS2 UCRT64 runtime libraries needed by WeasyPrint.

Downloads the `mingw-w64-ucrt-x86_64-pango` package and its full dependency
tree from the MSYS2 UCRT64 repository, then extracts them into C:\\msys64 so
that WeasyPrint finds the DLLs in its default search directory
(C:\\msys64\\ucrt64\\bin). No administrator rights required.
"""

import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

REPO_URL = "https://repo.msys2.org/mingw/ucrt64"
DEST = Path(r"C:\msys64")
ROOT_PACKAGE = "mingw-w64-ucrt-x86_64-pango"
PKG_RE = re.compile(r'href="([^"]+\.pkg\.tar\.(?:zst|xz))"')


def fetch_listing() -> dict[str, list[tuple[tuple[int, ...], int, str]]]:
    """Return {pkg_name: [(version_key, release, filename), ...]} for the repo."""
    print("Fetching repository listing...")
    with urllib.request.urlopen(f"{REPO_URL}/", timeout=60) as resp:
        html = resp.read().decode("utf-8", "replace")

    packages: dict[str, list[tuple[tuple[int, ...], int, str]]] = {}
    for raw_filename in PKG_RE.findall(html):
        filename = urllib.parse.unquote(raw_filename)
        # name-ver-rel-arch.pkg.tar.ext  ->  name, ver, rel
        m = re.match(r"^(.+)-([0-9][^-]*)-([0-9]+)-(?:any|x86_64)\.pkg\.tar\.", filename)
        if not m:
            continue
        name, ver, rel = m.group(1), m.group(2), int(m.group(3))
        ver = re.sub(r"^\d+:", "", ver)  # strip epoch
        nums = tuple(int(p) for p in re.findall(r"\d+", ver)[:4])
        packages.setdefault(name, []).append((nums, rel, filename))
    return packages


def version_key(entry: tuple) -> tuple:
    nums, rel = entry[0], entry[1]
    padded = nums + (0,) * (4 - len(nums))
    return padded + (rel,)


def read_pkginfo(pkg_path: Path) -> list[str]:
    out = subprocess.run(
        ["tar", "-xOf", str(pkg_path), ".PKGINFO"],
        capture_output=True, text=True, check=True,
    )
    depends = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if line.startswith("depend ="):
            dep = line.split("=", 1)[1].strip()
            # strip version constraint: foo>=1.2, foo=1.2-3, foo<2 ...
            dep = re.split(r"[=<>~^]", dep)[0].strip()
            if dep:
                depends.append(dep)
    return depends


def main() -> int:
    packages = fetch_listing()
    print(f"{len(packages)} packages indexed.")

    queue = [ROOT_PACKAGE]
    seen: set[str] = set()
    installed: list[str] = []
    missing: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        while queue:
            name = queue.pop(0)
            if name in seen:
                continue
            seen.add(name)

            versions = packages.get(name)
            if not versions:
                print(f"  !! NOT FOUND in repo: {name}")
                missing.append(name)
                continue

            best = max(versions, key=version_key)
            filename = best[2]
            url = f"{REPO_URL}/{filename}"
            pkg_path = Path(tmp) / filename
            print(f"  Downloading {filename} ...")
            urllib.request.urlretrieve(url, pkg_path)

            for dep in read_pkginfo(pkg_path):
                if dep not in seen:
                    queue.append(dep)

            print(f"  Extracting into {DEST} ...")
            subprocess.run(["tar", "-xf", str(pkg_path), "-C", str(DEST)], check=True)
            installed.append(filename)

    print(f"\nDone: {len(installed)} packages installed into {DEST}")
    if missing:
        print("Missing (may be OK if optional):")
        for name in missing:
            print(f"  - {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
