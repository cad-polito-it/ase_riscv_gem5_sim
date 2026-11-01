ASE Studio - RISC-V simulator (gem5) for Macs with Apple Silicon

INSTALLATION
  1. Drag "ASE Studio" into the Applications folder.
  2. First launch: the app is not signed by an Apple developer, so macOS
     blocks it. Open it once, then go to
     System Settings > Privacy & Security > "Open Anyway".
     Alternatively, from Terminal:
       xattr -dr com.apple.quarantine "/Applications/ASE Studio.app"

USE
  - ASE Studio opens in its own window; closing it also stops the server.
  - Your programs and results are in the "ASE Studio" folder inside your
    home folder (~/ASE Studio).
  - Updates: when a new version of ASE Studio, of the simulator files or of
    gem5 is available, the "Update" button appears; after updating, quit
    and reopen the app. Your programs and setup_default are never touched.
  - Log: ~/Library/Logs/ASE Studio.log

Nothing else needs to be installed: Python, gem5 and the RISC-V compiler
are included in the app.
