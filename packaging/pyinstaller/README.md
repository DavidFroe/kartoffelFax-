# PyInstaller packaging

Build from the repository root (needs `pip install -e ".[packaging]"`):

```bash
pyinstaller packaging/pyinstaller/kartoffelfax.spec
```

Result: single-file executable `dist/kartoffelfax` that serves the bundled
frontend. Ghostscript (`gs`) is **not** bundled and must be installed on the
target system.

Status: Linux build verified (binary starts, serves the UI, creates the DB and
encrypts credentials). The Windows build uses the same spec but has **not**
been tested.
