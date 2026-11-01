#!/usr/bin/env python3
"""Entry point of the standalone ASE Studio.app.

Runs ase_studio/backend.py without its Git checks (the app contains no Git
checkouts) and replaces the Git-based update with a component update that
downloads the latest sources from GitHub:

  * ASE Studio (backend + frontend) -> ~/Library/Application Support/ASE Studio/ase_studio
    (the launcher prefers it over the copy bundled in the app)
  * Simulator files (gem5 configs, programs/demo.mk, branch list) -> the workspace
  * gem5.opt (from the GitHub release named in versions.json, checked with
    gem5_selftest.py before use) -> ~/Library/Application Support/ASE Studio/gem5

A newer full app (a v<version> or v<version>-macos release of the repo in versions.json)
is announced with a link to its download page.

Python and the compiler are binaries: they only change with a new app.

Usage: ase_studio_app.py PORT | --check-startup
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

RES = Path(__file__).resolve().parent
SUPPORT = Path.home() / "Library/Application Support/ASE Studio"
UPDATED_STUDIO = SUPPORT / "ase_studio"
STUDIO = Path(os.environ.get("ASE_STUDIO_DIR") or RES / "ase_studio")
BUNDLED_VERSIONS = RES / "versions.json"
INSTALLED_VERSIONS = SUPPORT / "versions.json"
# An updated gem5.opt mirrors the bundle layout (Contents/Resources/gem5/build
# next to a Contents/Frameworks link), so its @executable_path reference to
# the bundled Python framework still resolves.
BUNDLED_GEM5_BUILD = RES / "gem5/build"
GEM5_UPDATE = SUPPORT / "gem5"
GEM5_UPDATE_BUILD = GEM5_UPDATE / "Contents/Resources/gem5/build"
GEM5_UPDATE_INFO = GEM5_UPDATE / "installed.json"

sys.path.insert(0, str(STUDIO))
sys.path.insert(1, str(RES))
import backend  # noqa: E402
import gem5_selftest  # noqa: E402

# Simulator files refreshed by an update. Student projects and setup_default
# are local data and are never touched.
SIMULATOR_FILES = ("gem5/", "programs/demo.mk", "ase_studio_branches.json")
CHECK_INTERVAL = 15 * 60          # GitHub allows 60 anonymous API calls per hour
_cache: dict = {}


def load_versions() -> dict:
    versions = json.loads(BUNDLED_VERSIONS.read_text())
    try:
        installed = json.loads(INSTALLED_VERSIONS.read_text())
    except (OSError, json.JSONDecodeError):
        installed = {}
    for key, commit in installed.items():
        if key in versions:
            versions[key]["commit"] = commit
    # The updated Studio is only in use if the launcher picked it.
    if STUDIO != UPDATED_STUDIO:
        versions["studio"]["commit"] = json.loads(BUNDLED_VERSIONS.read_text())["studio"]["commit"]
    if "gem5" in versions:
        versions["gem5"]["commit"] = gem5_update_info().get("id") or versions["gem5"]["commit"]
    return versions


# --------------------------------------------------------------- gem5 update
def bundled_gem5_id() -> str:
    return json.loads(BUNDLED_VERSIONS.read_text()).get("gem5", {}).get("commit", "")


def gem5_update_info() -> dict:
    """The downloaded gem5, if it was installed on top of this app's gem5.

    A newer app brings its own gem5: an update made for an older app is
    ignored (and replaced by the next update)."""
    try:
        info = json.loads(GEM5_UPDATE_INFO.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if info.get("bundled") != bundled_gem5_id() or not (
            GEM5_UPDATE_BUILD / "RISCV/gem5.opt").is_file():
        return {}
    link_frameworks(GEM5_UPDATE)
    return info


def link_frameworks(root: Path) -> None:
    """Point root/Contents/Frameworks at the running app (it may have moved)."""
    link = root / "Contents/Frameworks"
    target = RES.parent / "Frameworks"
    if link.is_symlink() and Path(os.readlink(link)) == target:
        return
    link.unlink(missing_ok=True)
    link.symlink_to(target)


def active_gem5_build() -> Path:
    return GEM5_UPDATE_BUILD if gem5_update_info() else BUNDLED_GEM5_BUILD


def gem5_check(build: Path) -> tuple[bool, str]:
    return gem5_selftest.check(build / "RISCV/gem5.opt", RES / "toolchain/bin")


def release_url(item: dict, name: str) -> str:
    return f"https://github.com/{item['repo']}/releases/download/{item['release']}/{name}"


def gem5_manifest(item: dict) -> dict | None:
    """The published gem5 update, or None if the release does not exist."""
    try:
        return json.loads(curl(release_url(item, "gem5.json")))
    except OSError as error:
        if "404" in str(error):
            return None
        raise


def install_gem5(item: dict, manifest: dict, into: Path) -> str:
    archive = into / manifest["asset"]
    archive.write_bytes(curl(release_url(item, manifest["asset"]), timeout=600))
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["sha256"]:
        raise OSError("the downloaded gem5 is corrupted (checksum mismatch)")
    staging = SUPPORT / "gem5.new"
    shutil.rmtree(staging, ignore_errors=True)
    riscv = staging / "Contents/Resources/gem5/build/RISCV"
    riscv.mkdir(parents=True)
    with tarfile.open(archive) as tar:
        member = tar.getmember("gem5.opt")
        if not member.isfile():
            raise OSError("the downloaded gem5 archive is invalid")
        (riscv / "gem5.opt").write_bytes(tar.extractfile(member).read())
    (riscv / "gem5.opt").chmod(0o755)
    link_frameworks(staging)
    ok, message = gem5_check(staging / "Contents/Resources/gem5/build")
    if not ok:
        shutil.rmtree(staging, ignore_errors=True)
        raise OSError(f"the downloaded gem5 failed its self-test: {message}")
    (staging / "installed.json").write_text(json.dumps(
        {"id": manifest["id"], "bundled": bundled_gem5_id()}, indent=2))
    old = SUPPORT / "gem5.old"
    shutil.rmtree(old, ignore_errors=True)
    if GEM5_UPDATE.exists():
        GEM5_UPDATE.rename(old)
    staging.rename(GEM5_UPDATE)
    shutil.rmtree(old, ignore_errors=True)
    return message


def gem5_health() -> tuple[bool, str]:
    """Self-test of the gem5 in use, run once per gem5 build."""
    build = active_gem5_build()
    key = (str(build), (build / "RISCV/gem5.opt").stat().st_mtime)
    if _cache.get("gem5_health", (None,))[0] != key:
        _cache["gem5_health"] = (key, gem5_check(build))
    return _cache["gem5_health"][1]


def save_installed(key: str, commit: str) -> None:
    SUPPORT.mkdir(parents=True, exist_ok=True)
    try:
        installed = json.loads(INSTALLED_VERSIONS.read_text())
    except (OSError, json.JSONDecodeError):
        installed = {}
    installed[key] = commit
    INSTALLED_VERSIONS.write_text(json.dumps(installed, indent=2))


def curl(*args: str, timeout: int = 20) -> bytes:
    # /usr/bin/curl uses the macOS trust store; the bundled Python has no CA file.
    result = subprocess.run(["/usr/bin/curl", "-fsSL", "--max-time", str(timeout), *args],
                            capture_output=True)
    if result.returncode:
        raise OSError(result.stderr.decode(errors="replace").strip() or "download failed")
    return result.stdout


def remote_commit(repo: str, branch: str) -> str:
    return curl("-H", "Accept: application/vnd.github.sha",
                f"https://api.github.com/repos/{repo}/commits/{branch}").decode().strip()


def release_version(tag: str) -> tuple[int, ...] | None:
    # One release can carry every platform (v1.5.0); older ones were tagged
    # per platform (v1.3.0-macos).
    match = re.fullmatch(r"v(\d+(?:\.\d+)*)(?:-macos)?", tag or "")
    return tuple(int(part) for part in match[1].split(".")) if match else None


def app_release(item: dict) -> dict | None:
    """The newest published app release, if it is newer than this app."""
    current = release_version(item.get("tag", ""))
    releases = json.loads(curl(f"https://api.github.com/repos/{item['repo']}/releases?per_page=30"))
    published = [(release_version(release.get("tag_name", "")), release)
                 for release in releases
                 if not release.get("draft") and not release.get("prerelease")]
    published = [(version, release) for version, release in published if version]
    if not current or not published:
        return None
    version, release = max(published, key=lambda pair: pair[0])
    if version <= current:
        return None
    return {"version": ".".join(map(str, version)), "tag": release["tag_name"],
            "name": release.get("name") or release["tag_name"], "url": release["html_url"]}


def update_status(refresh=False):
    if not refresh or time.time() - _cache.get("at", 0) < CHECK_INTERVAL:
        if "status" in _cache:
            return _cache["status"]
    repositories = []
    versions = load_versions()
    for key, item in versions.items():
        if key == "app":
            continue
        entry = {"label": item["label"], "path": item["repo"], "dirty": False,
                 "available": False, "key": key}
        try:
            if key == "gem5":
                repositories.append(gem5_status(item, entry))
                continue
            latest = remote_commit(item["repo"], item["branch"])
            entry["latest"] = latest
            entry["available"] = latest != item["commit"]
            entry["message"] = (f"{item['label']}: update available ({latest[:7]})."
                                if entry["available"] else f"{item['label']} is up to date.")
        except OSError as error:
            entry["message"] = f"{item['label']}: update check failed ({error})."
        repositories.append(entry)
    available = any(item["available"] for item in repositories)
    release = None
    if "app" in versions:
        try:
            release = app_release(versions["app"])
        except (OSError, ValueError, KeyError):
            release = None
    message = " ".join(item["message"] for item in repositories)
    if release:
        message += f" ASE Studio app {release['version']} is available."
    status = {"warning": any(item.get("warning") for item in repositories),
              "available": available, "canUpdate": available, "repositories": repositories,
              "appRelease": release, "message": message,
              "checkedAt": int(time.time())}
    _cache.update(status=status, at=time.time())
    return status


def gem5_status(item: dict, entry: dict) -> dict:
    healthy, health = gem5_health()
    manifest = gem5_manifest(item)
    if manifest and manifest["id"] != item["commit"]:
        entry.update(available=True, latest=manifest["id"], manifest=manifest,
                     message=f"gem5: update available ({manifest['id']}).")
    elif healthy:
        entry["message"] = "gem5 is up to date."
    else:
        entry.update(warning=True, message=(
            f"gem5: the gem5 in use is broken ({health}). No fix has been "
            "published yet: download a newer ASE Studio app."))
    if not healthy and entry["available"]:
        entry["message"] += f" It fixes the gem5 in use ({health})."
    return entry


def download_tree(repo: str, commit: str, into: Path) -> Path:
    archive = into / "source.tar.gz"
    archive.write_bytes(curl(f"https://codeload.github.com/{repo}/tar.gz/{commit}", timeout=300))
    with tarfile.open(archive) as tar:
        tar.extractall(into, filter="data") if hasattr(tarfile, "data_filter") else tar.extractall(into)
    archive.unlink()
    return next(p for p in into.iterdir() if p.is_dir())      # "<repo>-<commit>/"


def install_studio(source: Path) -> None:
    if not (source / "backend.py").is_file() or not (source / "frontend/index.html").is_file():
        raise OSError("the downloaded ASE Studio is incomplete")
    SUPPORT.mkdir(parents=True, exist_ok=True)
    staging = SUPPORT / "ase_studio.new"
    shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(source, staging, ignore=shutil.ignore_patterns(".git*", "__pycache__"))
    old = SUPPORT / "ase_studio.old"
    shutil.rmtree(old, ignore_errors=True)
    if UPDATED_STUDIO.exists():
        UPDATED_STUDIO.rename(old)
    staging.rename(UPDATED_STUDIO)
    shutil.rmtree(old, ignore_errors=True)


def install_simulator(source: Path) -> list[str]:
    changed = []
    for rel in SIMULATOR_FILES:
        src = source / rel
        files = [p for p in src.rglob("*") if p.is_file()] if rel.endswith("/") else [src]
        for path in files:
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            dst = backend.ROOT / relative
            if dst.is_file() and dst.read_bytes() == path.read_bytes():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
            changed.append(str(relative))
    return changed


def pull_update(discard_local_changes=False):
    status = update_status(refresh=True)
    if not status["available"]:
        return {"ok": True, "output": status["message"], "advancedOutput": status["message"]}
    versions = load_versions()
    outputs, ok = [], True
    for entry in status["repositories"]:
        if not entry["available"]:
            continue
        item = versions[entry["key"]]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                if entry["key"] == "gem5":
                    message = install_gem5(item, entry["manifest"], Path(tmp))
                    outputs.append(f"gem5: updated to {entry['latest']} ({message}).")
                    continue
                tree = download_tree(item["repo"], entry["latest"], Path(tmp))
                if entry["key"] == "studio":
                    install_studio(tree)
                    outputs.append(f"{item['label']}: updated to {entry['latest'][:7]}.")
                else:
                    changed = install_simulator(tree)
                    outputs.append(f"{item['label']}: updated to {entry['latest'][:7]}"
                                   + (":\n  " + "\n  ".join(changed) if changed else "."))
            save_installed(entry["key"], entry["latest"])
        except (OSError, tarfile.TarError, StopIteration) as error:
            ok = False
            outputs.append(f"{item['label']}: update failed: {error}")
    _cache.clear()
    message = "\n".join(outputs)
    if ok:
        message += "\n\nUpdate completed. Restart ASE Studio to load the new version."
    return {"ok": ok, "output": message, "advancedOutput": message, "restartRequired": ok}


def space_free(path: Path) -> Path:
    """Map a path to the space-free links made by launcher.sh.

    The course Makefiles use $(CC) and $(ASE_STUDIO_DEMO_MK) unquoted, while
    the app lives in "ASE Studio.app" and the workspace in "~/ASE Studio";
    the backend resolves symlinks, so undo that here."""
    if " " not in str(path):
        return path
    for variable in ("ASE_STUDIO_TOOLS", "ASE_STUDIO_WORKSPACE_LINK"):
        link = os.environ.get(variable)
        if link:
            real = Path(link).resolve()
            if path.is_relative_to(real):
                return Path(link) / path.relative_to(real)
    return path


# The backend opens editors and folders with Linux tools (xdg-open, GTK);
# on macOS the same actions go through /usr/bin/open.
def open_with_editor(name):
    source = backend.source_file(backend.project_dir(name))
    result = subprocess.run(["/usr/bin/open", "-t", str(source)], capture_output=True, text=True)
    if result.returncode:
        backend.fail(f"The file could not be opened: {result.stderr.strip()}", 500)
    return {"ok": True, "output": f"Opened {source.name} in the default text editor."}


def reveal_submission_folder(archive_path):
    if not isinstance(archive_path, str) or not archive_path:
        backend.fail("The submission archive path is missing.")
    archive = backend.resolve_environment_path(archive_path)
    try:
        archive.relative_to(backend.active_submission_directory())
    except ValueError:
        backend.fail("Invalid submission archive path.")
    if not archive.is_file() or archive.suffix.lower() != ".zip":
        backend.fail("The submission ZIP could not be found.", 404)
    result = subprocess.run(["/usr/bin/open", "-R", str(archive)], capture_output=True, text=True)
    if result.returncode:
        backend.fail(f"The submission folder could not be opened: {result.stderr.strip()}", 500)
    return {"ok": True, "output": f"Opened {archive.parent} in Finder."}


def main() -> int:
    if hasattr(backend, "settings_env"):
        make_env = backend.settings_env

        def settings_env():
            env = make_env()
            if env.get("ASE_STUDIO_DEMO_MK"):
                env["ASE_STUDIO_DEMO_MK"] = str(space_free(Path(env["ASE_STUDIO_DEMO_MK"])))
            # Run the updated gem5 wherever the settings name the bundled one,
            # as a build directory or (ASE Studio 1.4.2+) as the executable.
            configured = Path(env["GEM5_INSTALLATION_PATH"]).resolve()
            bundled = BUNDLED_GEM5_BUILD.resolve()
            if configured == bundled:
                env["GEM5_INSTALLATION_PATH"] = str(active_gem5_build())
            elif configured == (bundled / "RISCV/gem5.opt").resolve():
                env["GEM5_INSTALLATION_PATH"] = str(active_gem5_build() / "RISCV/gem5.opt")
            return env
        backend.settings_env = settings_env
    if hasattr(backend, "toolchain_executables"):
        find_toolchain = backend.toolchain_executables
        backend.toolchain_executables = lambda value: tuple(
            space_free(p) for p in find_toolchain(value))
    if hasattr(backend, "simulate"):
        run_simulation = backend.simulate

        def simulate(name):
            result = run_simulation(name)
            healthy, health = gem5_health()
            if not healthy and isinstance(result, dict):
                warning = (f"WARNING: this gem5 is broken, results may be wrong: {health}. "
                           "Use Update, or download a newer ASE Studio app.\n\n")
                for key in ("output", "advancedOutput"):
                    if isinstance(result.get(key), str):
                        result[key] = warning + result[key]
            return result
        backend.simulate = simulate
    backend.require_startup_repositories = lambda: None
    backend.update_status = update_status
    backend.pull_update = pull_update
    backend.open_with_editor = open_with_editor
    backend.reveal_submission_folder = reveal_submission_folder
    if "--check-startup" in sys.argv:
        print(f"ASE Studio {backend.STUDIO_VERSION} ({STUDIO})")
        return 0
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    try:
        server = backend.ThreadingHTTPServer(("127.0.0.1", port), backend.Handler)
    except OSError:
        server = backend.ThreadingHTTPServer(("127.0.0.1", 0), backend.Handler)
        print(f"Port {port} is already occupied; using a new port.", flush=True)
    print(f"ASE Studio: http://127.0.0.1:{server.server_address[1]}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
