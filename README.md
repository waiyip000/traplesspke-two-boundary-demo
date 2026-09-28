# TraplessPKE Two-Boundary demonstration 0.1.2

An inspectable, two-candidate Python demonstration: a sender selects one file,
encrypts using a public identity, and the recipient recovers the selected file
using the private identity. A separate exposure workflow reveals both decoded
candidates and the content capability while withholding the intent capability.

This is a reference demonstration, not the commercial TraplessPKE application.
Its complete selection mechanism is public. It has no hidden TraplessPKE backend,
online owner service or remote correctness oracle. Independent implementations
are permitted under [Apache-2.0](LICENSE). Copyright 2026 Wai Yip, WONG.
The separate commercial implementation is not included or licensed by this repo.

## Downloads and manual

Download the [Windows executable, source ZIP and offline Python kit](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2).
Read the [user manual](USER_MANUAL.md) before running a demonstration.
The standalone Windows ZIP needs no separate Python installation: extract the
whole archive and run `TraplessPKEDemo.exe --help` in PowerShell. It is a console
application. Keep its `_internal` directory alongside the executable.
[BUILD_WINDOWS.md](BUILD_WINDOWS.md) explains the public build recipe.

## Project links

[Research and project hub](https://github.com/waiyip000/TraplessPKE) · [Repository guide](PROJECT_MAP.md) · [Functional validation](VALIDATION.md).

The original research hub preserves the whitepaper, authorship chronology and
project context. Both repositories are now public following the owner's
publication instruction. This demo is self-contained;
its downloads, instructions and [IEEE paper link](https://ieeexplore.ieee.org/document/11366456)
do not require access to that repository.

## Research origin and implementation separation

Wai Yip Wong, "TraplessPKE: A Selector-Based, Oracleless, Post-Quantum
Cryptosystem," IEEE CCNC 2026, pp. 1-2,
[doi:10.1109/CCNC65079.2026.11366456](https://ieeexplore.ieee.org/document/11366456).
This repository publishes an independent experimental implementation for
inspection. It does not publish the commercial Windows desktop 1.1.4 code,
private build history, customer packages or internal construction records.
Apache-2.0 applies to the demo source; third-party components retain their terms.

## Install on Windows x64

Use **64-bit CPython 3.12**. In an extracted offline release kit:

```powershell
py -3.12 .\install.py --target 'D:\TraplessDemo'
```

Choose a new writable installation directory. The kit contains the app wheel and
four pinned dependency wheels; installation needs no network. Python itself is
not bundled. If interrupted, repeat with `--resume` and the same kit and target.
Do not move an installed virtual environment. Run commands using
`D:\TraplessDemo\demo.ps1`, substituting your installation path.

For the source-only repository, use a dedicated environment:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-windows-py312.lock
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
& .\.venv\Scripts\python.exe -m traplesspke_demo --help
```

`install.py` requires a complete offline kit with `KIT.json`; it is not the
source-only installation command. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
and [DEPENDENCIES.json](DEPENDENCIES.json) for separate dependency terms.

## Demonstrate selection and recovery

Use a separate private working folder and your own two candidate files:

```powershell
& 'D:\TraplessDemo\demo.ps1' keygen --private private.json --public public.json
& 'D:\TraplessDemo\demo.ps1' walkthrough --public public.json --private private.json --candidate first.bin --candidate second.bin --intended 1 --job owner-job
```

Index `0` selects the first file; `1` selects the second. The CLI separately
displays the full intended path and requests confirmation. Passwords are entered
privately. The walkthrough actually encrypts, recovers through the private-key
path and compares recovered bytes with the selected original. It also checks
the selected index when candidate bytes are identical. This owner demonstration
knows the answer and is not a blinded peer experiment.

For separate sender and receiver operation:

```powershell
& 'D:\TraplessDemo\demo.ps1' send --public public.json --candidate first.bin --candidate second.bin --intended 1 --out message.tbd
& 'D:\TraplessDemo\demo.ps1' receive --private private.json --bundle message.tbd --out recovered.bin
& 'D:\TraplessDemo\demo.ps1' compare-local second.bin recovered.bin
```

Sending uses no private identity. Receiving uses no original candidates, expected
hashes or expected index. Comparison is a separate owner operation. A keypair can
be reused for fresh sends. [WALKTHROUGH.md](WALKTHROUGH.md) explains stage resume,
retained private recovery files and Windows input sharing.

## Inspect the Two-Boundary view

With a **disposable demonstration identity**, expose real decoded content:

```powershell
& 'D:\TraplessDemo\demo.ps1' expose --private private.json --bundle message.tbd --view V1b --out content-view
& 'D:\TraplessDemo\demo.ps1' recover-content --authority content-view/content-authority.json --bundle content-view/bundle.tbd --out decoded-candidates
```

V1b intentionally discloses the content private key and actual decryption material.
Never use an identity protecting other private messages. The intent private key
and selected-index diagnostic are withheld. Read [PROTOCOL.md](PROTOCOL.md).

[PEER_EXCHANGE.md](PEER_EXCHANGE.md) describes new blinded challenges, separate
submission exchange and committed reveal. Keep the owner directory private;
share only the explicit public view. Local teaching predictions do not establish
independent peer ordering or a numerical security bound.

## Scope of the claims

This release offers functional controls and an inspectable hypothesis. **No
empirical security bound or universal unbreakability result is established.**
Both key capabilities use ML-KEM-768. Disclosing one content capability does not
demonstrate survival of a general primitive break affecting both. Meaningful
decoys, endpoint behavior, process memory and timing are separate limitations.
Read [THREAT_MODEL.md](THREAT_MODEL.md), [LIMITATIONS.md](LIMITATIONS.md),
[DISCLOSURE.md](DISCLOSURE.md), and [ACCEPTANCE.md](ACCEPTANCE.md).

This profile omits signatures, a GUI, commercial product internals and a numerical
attack campaign. Optional OpenCL producers create public synthetic inputs;
ordinary cryptography has no GPU dependency. Install the separate pinned GPU
requirements only to use those producers.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub](https://github.com/waiyip000/TraplessPKE)
