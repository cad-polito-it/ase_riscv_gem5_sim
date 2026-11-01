# ASE Studio.app – macOS build

`build_app.py` produces `dist/ASE Studio.app` and `dist/ASE-Studio-<version>.dmg`:
a self-contained app (Apple Silicon) with ASE Studio, gem5, Python 3.10, the
RISC-V compiler and GNU make. It runs on a Mac without Homebrew or the
Command Line Tools.

The build is done **once**, by whoever publishes a release; students download
the `.dmg`, drag the app into Applications and open it.

## Requirements (build machine only)

```sh
brew install python@3.10 riscv64-elf-gcc riscv64-elf-binutils make
git submodule update --init ase_studio
```

`clang` (Command Line Tools) is needed as well.

## Build

```sh
utils/macOS/build_gem5.sh                                                        # gem5.opt
/opt/homebrew/opt/python@3.10/bin/python3.10 utils/macOS/build_app.py            # app + dmg
/opt/homebrew/opt/python@3.10/bin/python3.10 utils/macOS/build_app.py --no-dmg   # app only
```

`build_gem5.sh` downloads gem5 into `tools/gem5` (if missing), applies the
patches in `gem5_patches/` and builds it. The patches are needed: on macOS
`uint_fast16_t` is 16 bits wide, and without `0001` every floating-point
operation of gem5 reads truncated operands (`1.5 * 2.0` gives NaN, see
cad-polito-it/ase_riscv_gem5_sim#36). `0002` fixes the build with recent
Apple clang. `build_app.py` refuses a `gem5.opt` that fails
`gem5_selftest.py`.

ASE Studio is taken from the `ase_studio` submodule (its committed HEAD);
`--studio-dir PATH` builds another checkout instead.

`build_app.py` copies every non-system library into `Contents/Frameworks`,
relinks it (`@executable_path` for executables, `@loader_path` for libraries
and Python modules), checks that no reference to `/opt/homebrew` is left and
signs everything ad hoc. The minimum macOS version of the app is the highest
one among the bundled binaries (Homebrew bottles use the build machine's).

## Releasing

```sh
gh release create v<version> "dist/ASE-Studio-<version>.dmg" \
    --title "ASE Studio <version> for macOS" --notes "..."
gh release create gem5-macos-arm64 --title "gem5 for ASE Studio (macOS)" \
    --notes "gem5.opt for the in-app update" || true
gh release upload gem5-macos-arm64 dist/gem5-macos-arm64.tar.gz dist/gem5.json --clobber
```

The app is not notarized: on first launch macOS asks for confirmation
(*System Settings → Privacy & Security → Open Anyway*).

## Updates inside the app

The app contains no git checkout, so the **Update** button downloads instead:

- ASE Studio from the GitHub repository of the `ase_studio` submodule, on the
  branch named in `ase_studio_branches.json`;
- the simulator files (`gem5/`, `programs/demo.mk`, `ase_studio_branches.json`)
  from `cad-polito-it/ase_riscv_gem5_sim`;
- `gem5.opt` from the `gem5-macos-arm64` release of the repository the app is
  built from, installed only after its checksum and `gem5_selftest.py` pass
  (otherwise the bundled gem5 stays in use).

A newer full app (a `v<version>` release) is announced with a link to its
download page. Python and the compiler change only with a new `.dmg`.

If the gem5 in use fails the self-test, every simulation output starts with
a warning.

## Files

| File | Role |
| --- | --- |
| `launcher.m` | App executable: native window (WKWebView), starts and stops the server |
| `launcher.sh` | Environment (app tools only), creates `~/ASE Studio`, runs the server |
| `ase_studio_app.py` | Runs `ase_studio/backend.py` without git checks; download-based update (gem5 included); "Open with" and the submission folder through macOS `open` |
| `build_gem5.sh`, `gem5_patches/` | Build `tools/gem5` for macOS with the required patches |
| `gem5_selftest.py` | Checks that gem5 computes floating point correctly (build, update and run time) |
| `Info.plist`, `AppIcon.icns`, `README.txt` | Bundle metadata, icon and the text shown in the `.dmg` |

## Where the data lives

- User projects: `~/ASE Studio` (created on first launch, never overwritten)
- Updated ASE Studio: `~/Library/Application Support/ASE Studio`
- Updated gem5: `~/Library/Application Support/ASE Studio/gem5`
- Log: `~/Library/Logs/ASE Studio.log`
