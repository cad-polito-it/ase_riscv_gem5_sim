#!/usr/bin/env python3
"""Build a self-contained "ASE Studio.app" and its .dmg (macOS, Apple Silicon).

The app is a native window (WKWebView, launcher.m) around the ASE Studio
backend and bundles the project template, gem5.opt, Python 3.10, the RISC-V
toolchain and GNU make. Every non-system library is copied into
Contents/Frameworks and relinked (executables via @executable_path, libraries
and Python modules via @loader_path), then everything is ad-hoc signed.

Build requirements (on the build machine only):
  brew install python@3.10 riscv64-elf-gcc riscv64-elf-binutils make
  tools/gem5/build/RISCV/gem5.opt compiled by utils/macOS/build_gem5.sh

Usage:  utils/macOS/build_app.py [--no-dmg] [--simulator-repo OWNER/REPO]
                                 [--gem5-repo OWNER/REPO] [--studio-dir PATH]
Output: dist/ASE Studio.app, dist/ASE-Studio-<version>.dmg and the gem5
        update for the app (dist/gem5-macos-arm64.tar.gz + dist/gem5.json,
        to attach to the GitHub release named GEM5_RELEASE)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tarfile
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DIST = REPO / "dist"
APP = DIST / "ASE Studio.app"
CONTENTS = APP / "Contents"
RES = CONTENTS / "Resources"
FRAMEWORKS = CONTENTS / "Frameworks"
PYFW = FRAMEWORKS / "Python.framework"
PYVER = PYFW / "Versions" / "3.10"

BREW = Path(subprocess.run(["brew", "--prefix"], capture_output=True, text=True,
                           check=True).stdout.strip())
BREW_PYFW = BREW / "opt/python@3.10/Frameworks/Python.framework/Versions/3.10"
GCC = BREW / "opt/riscv64-elf-gcc"
BINUTILS = BREW / "opt/riscv64-elf-binutils"
GMAKE = BREW / "opt/make/bin/gmake"
GEM5 = REPO / "tools/gem5"
GEM5_PATCHES = HERE / "gem5_patches"
# GitHub release (in --gem5-repo) that carries the gem5 update of the app.
GEM5_RELEASE = "gem5-macos-arm64"
GEM5_ASSET = DIST / f"{GEM5_RELEASE}.tar.gz"
# Where the app looks for updates. The simulator files follow the official
# repository whatever clone the app is built from; the gem5 update comes from
# the release of the repository that publishes the macOS builds.
SIMULATOR_REPO = "cad-polito-it/ase_riscv_gem5_sim"
# ASE Studio comes from the ase_studio submodule; the in-app update follows
# its GitHub repository and the branch named in ase_studio_branches.json.
# New full apps are GitHub releases tagged v<version>, which the app announces.
STUDIO_DIR = REPO / "ase_studio"
STUDIO_SRC = DIST / "ase_studio-src"
APP_RELEASE_TAG = "v{version}"
_studio: dict = {}
GEM5_MANIFEST = DIST / "gem5.json"

sys.path.insert(0, str(HERE))
import gem5_selftest  # noqa: E402

# Files of the project that are copied into the user's workspace.
PROJECT_PATHS = ["programs", "gem5", "setup_default", "ase_studio_branches.json",
                 "simulate.py", "simulate.sh", "README.md", "LICENSE"]
# Parts of the toolchain a C/asm-only course never uses.
TOOLCHAIN_SKIP = {"cc1plus", "lto1", "riscv64-elf-lto-dump", "riscv64-elf-c++",
                  "riscv64-elf-g++", "plugin", "install-tools"}

LSREGISTER = ("/System/Library/Frameworks/CoreServices.framework/Frameworks/"
              "LaunchServices.framework/Support/lsregister")
MACHO_MAGICS = {b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe"}
SYSTEM_PREFIXES = ("/usr/lib/", "/System/")


def log(message: str) -> None:
    print(f"\033[1;34m==>\033[0m {message}", flush=True)


def run(*cmd, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], check=True, **kwargs)


def output(*cmd) -> str:
    return subprocess.run([str(c) for c in cmd], check=True, capture_output=True,
                          text=True).stdout


def copytree(src: Path, dst: Path, skip=frozenset()) -> None:
    shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True,
                    ignore=lambda _d, names: [n for n in names
                                              if n in skip or n in {"__pycache__", ".DS_Store"}])


# --------------------------------------------------------------- bundle layout
def check_inputs() -> None:
    missing = [p for p in (BREW_PYFW / "Python", GCC / "bin/riscv64-elf-gcc",
                           BINUTILS / "riscv64-elf/bin/as", GMAKE,
                           GEM5 / "build/RISCV/gem5.opt", GEM5 / "configs")
               if not p.exists()]
    if missing:
        sys.exit("Missing:\n  " + "\n  ".join(map(str, missing)))
    ok, message = gem5_selftest.check(GEM5 / "build/RISCV/gem5.opt", GCC / "bin")
    if not ok:
        sys.exit(f"gem5.opt is not usable: {message}\n"
                 "Rebuild it with utils/macOS/build_gem5.sh")
    log(f"gem5: {message}")


def studio_version() -> str:
    return (STUDIO_SRC / "VERSION").read_text().strip()


def prepare_studio(local_dir: str | None) -> None:
    """Export the committed ASE Studio sources the app is built from.

    The ase_studio submodule is used unless --studio-dir names another
    checkout. Only its HEAD commit is bundled, never local edits, so the
    updater can compare it with the published branch."""
    source = Path(local_dir).resolve() if local_dir else STUDIO_DIR
    if not (source / "backend.py").is_file():
        sys.exit(f"{source} does not contain ASE Studio: run "
                 "git submodule update --init ase_studio, or use --studio-dir")
    commit = output("git", "-C", source, "rev-parse", "HEAD").strip()
    if output("git", "-C", source, "status", "--porcelain", "--untracked-files=no").strip():
        log(f"Warning: {source} has uncommitted changes, only HEAD is bundled")
    branch = json.loads((REPO / "ase_studio_branches.json").read_text())["studio"]
    repo = github_repo(source)
    log(f"ASE Studio from {repo}@{branch} ({commit[:7]})")
    archive = subprocess.run(["git", "-C", str(source), "archive", "--format=tar", commit],
                             check=True, capture_output=True).stdout
    if STUDIO_SRC.exists():
        shutil.rmtree(STUDIO_SRC)
    STUDIO_SRC.mkdir(parents=True)
    with tarfile.open(fileobj=BytesIO(archive)) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(STUDIO_SRC, filter="data")
        else:
            tar.extractall(STUDIO_SRC)
    _studio.update(repo=repo, branch=branch, commit=commit)


def make_skeleton() -> None:
    log(f"Creating {APP.relative_to(REPO)}")
    if APP.exists():
        shutil.rmtree(APP)
    for d in (CONTENTS / "MacOS", RES / "bin", FRAMEWORKS):
        d.mkdir(parents=True)
    run("clang", "-fobjc-arc", "-O2", "-arch", "arm64", "-mmacosx-version-min=11.3",
        "-framework", "Cocoa", "-framework", "WebKit",
        "-o", CONTENTS / "MacOS/ASEStudio", HERE / "launcher.m")
    for name in ("launcher.sh", "ase_studio_app.py", "gem5_selftest.py"):
        shutil.copy2(HERE / name, RES / name)
    shutil.copy2(HERE / "AppIcon.icns", RES / "AppIcon.icns")


def copy_project(simulator_repo: str, gem5_repo: str) -> None:
    log("Project template and ASE Studio")
    tracked = output("git", "-C", REPO, "ls-files", "--", *PROJECT_PATHS).splitlines()
    for rel in tracked:
        src = REPO / rel
        if src.is_file():
            dst = RES / "project" / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    copytree(STUDIO_SRC, RES / "ase_studio", skip={".git", ".gitignore"})
    write_versions(simulator_repo, gem5_repo)


def github_repo(path: Path) -> str:
    url = output("git", "-C", path, "remote", "get-url", "origin").strip()
    return re.sub(r"^.*github\.com[:/]|\.git$", "", url)


def write_versions(simulator_repo: str, gem5_repo: str) -> None:
    """Sources the app was built from; the in-app updater compares against them."""
    branches = json.loads((REPO / "ase_studio_branches.json").read_text())
    versions = {
        "studio": {"label": "ASE Studio", "repo": _studio["repo"],
                   "branch": _studio["branch"], "commit": _studio["commit"]},
        "simulator": {"label": "Simulator", "repo": simulator_repo,
                      "branch": branches["simulator"], "commit": ""},
    }
    versions["simulator"]["commit"] = simulator_commit(simulator_repo, branches["simulator"])
    versions["gem5"] = {"label": "gem5", "repo": gem5_repo,
                        "release": GEM5_RELEASE, "commit": gem5_build_id()}
    versions["app"] = {"label": "ASE Studio app", "repo": gem5_repo,
                       "tag": APP_RELEASE_TAG.format(version=studio_version())}
    (RES / "versions.json").write_text(json.dumps(versions, indent=2) + "\n")


def simulator_commit(repo: str, branch: str) -> str:
    """The commit of `repo` this clone is based on.

    A fork has its own merge commits, which the official repository does not
    know: compare against the last official commit already in this clone, or
    the app would offer an update right away."""
    for remote in output("git", "-C", REPO, "remote").split():
        url = output("git", "-C", REPO, "remote", "get-url", remote).strip()
        if re.sub(r"^.*github\.com[:/]|\.git$", "", url) == repo:
            run("git", "-C", REPO, "fetch", "--quiet", remote, branch)
            return output("git", "-C", REPO, "merge-base", "HEAD", "FETCH_HEAD").strip()
    return output("git", "-C", REPO, "rev-parse", "HEAD").strip()


def gem5_build_id() -> str:
    """gem5 source commit plus the macOS patches applied on top of it."""
    commit = output("git", "-C", GEM5, "rev-parse", "HEAD").strip()
    patches = hashlib.sha256()
    for patch in sorted(GEM5_PATCHES.glob("*.patch")):
        patches.update(patch.read_bytes())
    return f"{commit[:12]}+{patches.hexdigest()[:12]}"


def copy_gem5() -> None:
    log("gem5")
    dst = RES / "gem5/build/RISCV"
    dst.mkdir(parents=True)
    shutil.copy2(GEM5 / "build/RISCV/gem5.opt", dst / "gem5.opt")
    copytree(GEM5 / "configs", RES / "gem5/configs")


def copy_python() -> None:
    log("Python 3.10")
    copytree(BREW_PYFW, PYVER, skip={"test", "idlelib", "IDLE 3.app"})
    site = PYVER / "lib/python3.10/site-packages"
    if site.is_symlink():          # Homebrew points it outside the keg
        site.unlink()
        site.mkdir()
    (PYFW / "Versions/Current").symlink_to("3.10")
    for name in ("Python", "Resources", "Headers"):
        (PYFW / name).symlink_to(f"Versions/Current/{name}")
    (RES / "bin/python3").symlink_to("../../Frameworks/Python.framework/Versions/3.10/bin/python3.10")


def copy_toolchain() -> None:
    log("RISC-V toolchain (gcc + binutils) and GNU make")
    tc = RES / "toolchain"
    for sub in ("bin", "lib", "libexec"):
        copytree(GCC / sub, tc / sub, skip=TOOLCHAIN_SKIP)
    copytree(BINUTILS / "bin", tc / "bin")
    copytree(BINUTILS / "riscv64-elf", tc / "riscv64-elf")
    for la in tc.rglob("*.la"):
        la.unlink()
    shutil.copy2(GMAKE, RES / "bin/make")
    # /usr/bin/git is a stub that pops up the Command Line Tools installer.
    git = RES / "bin/git"
    git.write_text('#!/bin/bash\n'
                   '/usr/bin/xcode-select -p >/dev/null 2>&1 && exec /usr/bin/git "$@"\n'
                   'echo "git is not available (Command Line Tools not installed)" >&2\n'
                   'exit 1\n')
    git.chmod(0o755)


def write_info_plist(min_os: str) -> None:
    text = (HERE / "Info.plist").read_text().replace("__VERSION__", studio_version())
    info = plistlib.loads(text.encode())
    info["LSMinimumSystemVersion"] = min_os
    (CONTENTS / "Info.plist").write_bytes(plistlib.dumps(info))


# --------------------------------------------------------------- relinking
def is_macho(path: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    with open(path, "rb") as f:
        return f.read(4) in MACHO_MAGICS


def macho_type(path: Path) -> str:
    header = output("otool", "-hv", path).splitlines()[-1].split()
    return header[4]                     # EXECUTE / DYLIB / BUNDLE ...


def linked_libs(path: Path) -> list[str]:
    lines = output("otool", "-L", path).splitlines()[1:]
    return [line.strip().split(" (")[0] for line in lines]


def rpaths(path: Path) -> list[str]:
    text = output("otool", "-l", path)
    return re.findall(r"cmd LC_RPATH\n\s+cmdsize \d+\n\s+path (.+?) \(offset", text)


def bundled_target(dep: str) -> Path | None:
    """Where a non-system dependency lives inside the bundle (copying it if needed)."""
    if dep.startswith(SYSTEM_PREFIXES) or dep.startswith("@"):
        return None
    if "Python.framework/Versions/3.10/Python" in dep:
        return PYVER / "Python"
    src = Path(dep).resolve()
    if not src.exists():
        raise SystemExit(f"Library not found: {dep}")
    dst = FRAMEWORKS / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
        dst.chmod(0o755)
    return dst


def relink_all() -> None:
    log("Relinking libraries (@executable_path / @loader_path)")
    done: set[Path] = set()
    while True:
        pending = [p for p in APP.rglob("*") if p not in done and is_macho(p)]
        if not pending:
            break
        for path in pending:
            done.add(path)
            kind = macho_type(path)
            anchor = "@executable_path" if kind == "EXECUTE" else "@loader_path"
            args = []
            if kind == "DYLIB":
                own_id = linked_libs(path)[0] if path.name != "ASEStudio" else ""
                if path == PYVER / "Python":
                    args += ["-id", "@rpath/Python.framework/Versions/3.10/Python"]
                elif own_id and not own_id.startswith(SYSTEM_PREFIXES):
                    args += ["-id", f"@rpath/{path.name}"]
            for dep in linked_libs(path):
                target = bundled_target(dep)
                if target is None or target == path:
                    continue
                rel = os.path.relpath(target, path.parent)
                args += ["-change", dep, f"{anchor}/{rel}"]
            for rp in rpaths(path):
                if not rp.startswith("@"):
                    args += ["-delete_rpath", rp]
            if args:
                subprocess.run(["install_name_tool", *args, str(path)], check=True,
                               stderr=subprocess.DEVNULL)


def min_macos_version() -> str:
    versions = set()
    for path in APP.rglob("*"):
        if is_macho(path):
            versions.update(re.findall(r"minos (\d+\.\d+)", output("otool", "-l", path)))
    return max(versions | {"11.3"}, key=lambda v: tuple(map(int, v.split("."))))


# --------------------------------------------------------------- signing
def sign() -> None:
    log("Ad-hoc signing")
    machos = [p for p in APP.rglob("*") if is_macho(p)]
    # Inside-out: deepest files first, then nested bundles, then the app.
    for path in sorted(machos, key=lambda p: -len(p.parts)):
        if path.parent.name == "MacOS" and path.parent.parent.name == "Contents":
            continue                           # main executables: signed with their bundle
        run("codesign", "--force", "--sign", "-", "--timestamp=none", path,
            stderr=subprocess.DEVNULL)
    for bundle in (PYVER / "Resources/Python.app", PYVER, APP):
        run("codesign", "--force", "--sign", "-", "--timestamp=none", bundle,
            stderr=subprocess.DEVNULL)
    run("codesign", "--verify", "--deep", "--strict", APP)
    # The bundle folder existed before Info.plist and the icon were written:
    # make Finder/Dock pick up the icon instead of a cached generic one.
    run("touch", APP)
    subprocess.run([LSREGISTER, "-f", str(APP)], check=False)


def audit() -> None:
    log("Checking that nothing points outside the app")
    bad = []
    for path in APP.rglob("*"):
        if is_macho(path):
            for dep in linked_libs(path)[1:] + rpaths(path):
                if not dep.startswith(SYSTEM_PREFIXES) and not dep.startswith("@"):
                    bad.append(f"{path.relative_to(APP)} -> {dep}")
    if bad:
        raise SystemExit("References not relinked:\n  " + "\n  ".join(bad))


# --------------------------------------------------------------- gem5 update
def make_gem5_update() -> None:
    """Package the relinked, signed gem5.opt for the in-app gem5 update.

    The updater installs it under Application Support next to a link to the
    app's Frameworks, so @executable_path still finds the bundled Python."""
    gem5 = RES / "gem5/build/RISCV/gem5.opt"
    log(f"gem5 update: {GEM5_ASSET.relative_to(REPO)}")
    with tarfile.open(GEM5_ASSET, "w:gz") as tar:
        tar.add(gem5, arcname="gem5.opt")
    manifest = {"id": gem5_build_id(), "asset": GEM5_ASSET.name,
                "sha256": hashlib.sha256(GEM5_ASSET.read_bytes()).hexdigest(),
                "app": studio_version()}
    GEM5_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


# --------------------------------------------------------------- dmg
def make_dmg() -> Path:
    dmg = DIST / f"ASE-Studio-{studio_version()}.dmg"
    log(f"Creating {dmg.relative_to(REPO)}")
    staging = DIST / "dmg"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    run("ditto", APP, staging / APP.name)
    (staging / "Applications").symlink_to("/Applications")
    shutil.copy2(HERE / "README.txt", staging / "README.txt")
    dmg.unlink(missing_ok=True)
    run("hdiutil", "create", "-volname", "ASE Studio", "-srcfolder", staging,
        "-fs", "HFS+", "-format", "ULFO", "-ov", dmg, stdout=subprocess.DEVNULL)
    shutil.rmtree(staging)
    run("codesign", "--force", "--sign", "-", dmg)
    return dmg


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-dmg", action="store_true", help="build only the .app")
    parser.add_argument("--simulator-repo", default=SIMULATOR_REPO,
                        help=f"GitHub repo of the simulator updates (default {SIMULATOR_REPO})")
    parser.add_argument("--gem5-repo", default=None,
                        help="GitHub repo whose release carries the gem5 update "
                             "(default: this clone's origin)")
    parser.add_argument("--studio-dir", default=None,
                        help="build ASE Studio from this checkout instead of the ase_studio submodule")
    args = parser.parse_args()

    check_inputs()
    prepare_studio(args.studio_dir)
    make_skeleton()
    copy_project(args.simulator_repo, args.gem5_repo or github_repo(REPO))
    copy_gem5()
    copy_python()
    copy_toolchain()
    relink_all()
    audit()
    min_os = min_macos_version()
    write_info_plist(min_os)
    sign()
    size = output("du", "-sh", APP).split()[0]
    log(f"App ready: {APP} ({size}, requires macOS {min_os}+)")
    make_gem5_update()
    if not args.no_dmg:
        dmg = make_dmg()
        log(f"DMG ready: {dmg} ({output('du', '-sh', dmg).split()[0]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
