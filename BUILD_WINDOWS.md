# Building the public Windows executable

This executable contains only the public TraplessPKE demo 0.1.2 and its runtime dependencies. It contains no commercial 1.1.4 backend. Its algorithms are the same as the published Python modules; the carrier is a PyInstaller console application.

Use Windows x64, CPython 3.12.11 and a fresh virtual environment. Install the dependencies from requirements-windows-py312.lock, then PyInstaller 6.22.3. Run from the public source root:

```powershell
python -m PyInstaller --noconfirm --onedir --console --name TraplessPKEDemo --paths src --collect-all pqcrypto --copy-metadata cryptography --copy-metadata pqcrypto --hidden-import _cffi_backend --add-data 'src/traplesspke_demo;traplesspke_demo' launcher.py
```

Keep the entire dist/TraplessPKEDemo directory together, including _internal. The source modules are deliberately included so the owner walkthrough retains its source-bound resume records. Retain the Python licence, demo LICENSE/NOTICE and dependency notices when distributing a build.

BUILD_REQUIREMENTS.txt in the binary archive records the actual build environment. The optional OpenCL image producers remain a source-installation workflow; the executable does not bundle that optional GPU stack. The executable is unsigned; it is not a commercial product signature or certification. Source and executable behavior are inspectable, but this is not a claim of byte-for-byte reproducible builds.

## Published carrier and inspection

Get the tested executable from [v0.1.2 downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2);
[VALIDATION.md](VALIDATION.md) identifies its SHA-256 and tested behavior.
The distributed Windows 10/11 carrier uses the operating-system Universal CRT
and omits local `ucrtbase.dll` and `api-ms-win-*.dll` copies. The command above
is the PyInstaller construction step; retain the archive's runtime licences and
notices when assembling a distributable directory. A self-built executable is
a distinct artifact and does not inherit the published binary's test record.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub — currently private](https://github.com/waiyip000/TraplessPKE)
