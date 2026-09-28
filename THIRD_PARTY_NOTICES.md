# Dependency source and notice mapping

No third-party implementation is copied into the demo source tree. Installation
uses published binary wheels whose primitive sources remain inspectable. A native
primitive library is not a hidden TraplessPKE-specific implementation.

| Package | Role | Primary source |
|---|---|---|
| pqcrypto 0.3.4 | ML-KEM-768 primitive, historical API `generate_keypair/encrypt/decrypt` | [Versioned distribution](https://pypi.org/project/pqcrypto/0.3.4/) |
| cryptography 50.0.1 | AES-GCM-SIV, HKDF-SHA256, scrypt | [Project](https://github.com/pyca/cryptography), [AEAD API](https://cryptography.io/en/latest/hazmat/primitives/aead/) |
| cffi, pycparser | Primitive binding dependencies | Installed wheel metadata and included notices |
| pyopencl 2026.1.4 | Optional public-input OpenCL producer | [Project](https://github.com/inducer/pyopencl) |
| numpy, pytools, platformdirs, siphash24, typing_extensions | Optional producer dependencies | Installed wheel metadata and included notices |

`DEPENDENCIES.json` records installed versions, source URLs, available licence
expressions, wheel hashes and actual distributed licence/notice file locations.
Those notices are retained under `notices/`. The two platform-specific lock files
bind all installed core/optional dependencies to their downloaded artifact hashes.
The internal detached construction job also retains a dependency stage and the
pip installation report. The demo's owner-selected Apache-2.0 licence does not
replace these third-party terms.

Do not infer a historical release's API or licence from the current repository's
latest default branch. The dependency map for the exact installed 0.3.4 release
controls over generic/current pqcrypto descriptions. No claim of unconditional
licence clearance or source provenance is made by this table.

[Demo LICENSE](LICENSE) · [Demo NOTICE](NOTICE) · [Dependency manifest](DEPENDENCIES.json) · [Build instructions](BUILD_WINDOWS.md).

The [research repository's licensing explanation](https://github.com/waiyip000/TraplessPKE/blob/main/LICENSING.md)
concerns a separate repository and currently requires access. The demo's own
licence and included notices are available here without that access.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub — currently private](https://github.com/waiyip000/TraplessPKE)
