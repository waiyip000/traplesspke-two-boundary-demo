# TraplessPKE Two-Boundary demonstration 0.1.4

An inspectable, two-candidate Python demonstration: a sender selects one file,
encrypts using a public identity, and the recipient recovers the selected file
using the private identity. A separate exposure workflow reveals both decoded
candidates and the content capability while withholding the intent capability.

This is an inspectable reference demonstration of TraplessPKE.
Its complete selection mechanism is public. It has no hidden TraplessPKE backend,
online owner service or remote correctness oracle. Independent implementations
are permitted under [Apache-2.0](LICENSE). Copyright 2026 Wai Yip, WONG.

## Purpose and correctness

Demonstration 0.1.4 is corrected and functionally validated for its stated purposes:
showing public-key selection and exact recovery, exposing the content/intent
boundary, and supplying inspectable mathematics and algorithms for independent
expert review, testing and attacks. This release addresses implementation
correctness in those workflows. The cryptographic construction and two-candidate
wire format remain unchanged. Functional correctness is not a proof of
cryptographic security; read the protocol, threat model and limitations.

## Downloads

Download the [Windows executable, source and offline Python kit](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.4).
Read [USER_MANUAL.md](USER_MANUAL.md). Extract the complete standalone Windows ZIP
and keep `TraplessPKEDemo.exe` beside its `_internal` directory. No separate Python
installation is required for that executable. It is an unsigned console application.
[BUILD_WINDOWS.md](BUILD_WINDOWS.md) describes the public build recipe.
[VALIDATION.md](VALIDATION.md) summarizes the recorded finite functional scope.

## Install on Windows x64

Use **64-bit CPython 3.12**. In an extracted offline release kit:

```powershell
py -3.12 .\install.py --target 'D:\TraplessDemo'
```

Choose a new writable installation directory. The kit contains the app wheel and
four pinned dependency wheels; installation needs no network. Python itself is
not bundled. Resume with `--resume` and the same kit and target only when a bound
stage is acknowledged. An unacknowledged environment or pip attempt is preserved
and refused; use an explicitly new successor target. Completed resume verifies
the actual pinned payload bytes and launcher without reinstalling.
Do not move an installed virtual environment. Run commands using
`D:\TraplessDemo\env\Scripts\trapless-demo.exe`, substituting your installation path.

The generated console executable or `env\Scripts\python.exe -I -B -m
traplesspke_demo` is the default route. `demo.ps1` is optional: an unsigned
PowerShell script on a network share may be refused by host execution policy.
This distribution does not change machine or user policy.

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
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' keygen --private private.json --public public.json
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' walkthrough --public public.json --private private.json --candidate first.bin --candidate second.bin --intended 1 --job owner-job
```

Index `0` selects the first file; `1` selects the second. The CLI separately
displays the full intended path and requests confirmation. Passwords are entered
privately. The walkthrough actually encrypts, recovers through the private-key
path and compares recovered bytes with the selected original. It also checks
the selected index when candidate bytes are identical. This owner demonstration
knows the answer and is not a blinded peer experiment.

For separate sender and receiver operation:

```powershell
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' send --public public.json --candidate first.bin --candidate second.bin --intended 1 --out message.tbd
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' receive --private private.json --bundle message.tbd --out recovered.bin
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' compare-local second.bin recovered.bin
```

Sending uses no private identity. Receiving uses no original candidates, expected
hashes or expected index. Comparison is a separate owner operation. A keypair can
be reused for fresh sends. [WALKTHROUGH.md](WALKTHROUGH.md) explains stage resume,
retained private recovery files and Windows input sharing.

## Inspect the Two-Boundary view

With a **disposable demonstration identity**, expose real decoded content:

```powershell
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' expose --private private.json --bundle message.tbd --view V1b --out content-view
& 'D:\TraplessDemo\env\Scripts\trapless-demo.exe' recover-content --authority content-view/content-authority.json --bundle content-view/bundle.tbd --out decoded-candidates
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

This profile omits signatures, a GUI and a numerical
attack campaign. Optional OpenCL producers create public synthetic inputs;
ordinary cryptography has no GPU dependency. Install the separate pinned GPU
requirements only to use those producers.


