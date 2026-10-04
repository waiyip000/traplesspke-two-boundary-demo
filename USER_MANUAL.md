# TraplessPKE Two-Boundary demonstration — user manual

Application 0.1.4; Windows x64 demonstration release. Copyright 2026 Wai Yip, WONG. Demo source: Apache-2.0. This demonstration is self-contained and has no hidden backend.

[Download demo 0.1.4](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.4) · [Demo source](https://github.com/waiyip000/traplesspke-two-boundary-demo) · [Repository guide](PROJECT_MAP.md).

The [original research hub](https://github.com/waiyip000/TraplessPKE) is now public following the owner's publication instruction.
You do not need access to it to use or examine this demonstration.

## Choose a download

- **Windows executable ZIP:** extract the complete archive. Keep TraplessPKEDemo.exe and _internal together. No separate Python installation is required. This is a command-line application, with no GUI.
- **Source ZIP / repository:** inspect all demo algorithms and use the source installation in [README.md](README.md). Requires 64-bit CPython 3.12 and the pinned dependencies.
- **Offline Python kit:** extract completely and run install.py as described in README.md. Python itself is not included in that kit.

Use a separate private working directory with synthetic files and a disposable identity. Verify a download against the release SHA256SUMS.txt using Get-FileHash. The executable is unsigned; no publisher-signing certificate is claimed.

## Start the executable

Open PowerShell inside the extracted TraplessPKEDemo directory:

```powershell
.\TraplessPKEDemo.exe --help
.\TraplessPKEDemo.exe --version
```

For a source installation, replace .\TraplessPKEDemo.exe in subsequent commands with python -m traplesspke_demo. For an installed offline kit, use `env\Scripts\trapless-demo.exe`; `demo.ps1` is optional and subject to host policy. Use full paths if your private files are elsewhere.

## Create a reusable identity

```powershell
.\TraplessPKEDemo.exe keygen --private private.json --public public.json
```

Enter a password and repeat it. Keep private.json and the password private. Share public.json with the sender. Passwords are requested interactively; do not put them in command arguments. There is no forgotten-password recovery service.

To export the public identity again:

```powershell
.\TraplessPKEDemo.exe export-public --private private.json --out public-copy.json
```

## Demonstrate actual encryption, recovery and comparison

Prepare exactly two files, first.bin and second.bin. The following selects the second file (index 1):

```powershell
.\TraplessPKEDemo.exe walkthrough --public public.json --private private.json --candidate first.bin --candidate second.bin --intended 1 --job owner-job
```

The CLI displays the full selected path and asks for confirmation and the identity password. It actually encrypts, recovers through private-key operations and compares bytes with the original selection. Index 0 selects the first file. This owner walkthrough knows the answer and is not a blinded security experiment.

Use a new 0.1.4 job; older jobs retain their original source binding and must use their original version. Keep owner-job private: it contains selection records, paths, hashes, recovered plaintext and intermediate material. For an interrupted walkthrough, repeat the identical command with --resume. Keep the same inputs, identity, index, program and dependencies. Completed compatible stages are reused; changed or damaged bindings are refused.

## Separate sender and recipient

Sender, using only the public identity:

```powershell
.\TraplessPKEDemo.exe send --public public.json --candidate first.bin --candidate second.bin --intended 1 --out message.tbd
```

Recipient, without original candidate files or a supplied expected index:

```powershell
.\TraplessPKEDemo.exe receive --private private.json --bundle message.tbd --out recovered.bin
```

The owner can independently compare the recovered output:

```powershell
.\TraplessPKEDemo.exe compare-local second.bin recovered.bin
```

Keys are reusable for fresh sends. The selected index is fixed before finalizing a bundle. The program does not implement timed release or remote revocation.

## Inspect the content-exposure boundary

Use a disposable identity that protects no other messages:

```powershell
.\TraplessPKEDemo.exe expose --private private.json --bundle message.tbd --view V1b --out content-view
.\TraplessPKEDemo.exe recover-content --authority content-view/content-authority.json --bundle content-view/bundle.tbd --out decoded-candidates
```

V0 exports the public identity and bundle. V1a adds both actually decoded candidates. V1b also discloses the content private key and actual decoding material. Intent authority and owner selected-index records are excluded from that export. Do not share the owner directory or private identity.

Both capabilities use ML-KEM-768. Content-key disclosure is not the same experiment as a general break of the shared primitive. The explicit export is not a full-process memory dump. See [PROTOCOL.md](PROTOCOL.md), [THREAT_MODEL.md](THREAT_MODEL.md) and [LIMITATIONS.md](LIMITATIONS.md).

## Independent examination and reports

Experts may inspect and modify the demo under Apache-2.0 and conduct local analysis on their own disposable inputs. [PEER_EXCHANGE.md](PEER_EXCHANGE.md) describes committed challenges, independent predictions and reveal accounting. It does not authorize testing third-party services or operational transport systems. No public decryption/guess-confirmation service is provided.

Report findings through the [dedicated demo repository's Issues](https://github.com/waiyip000/traplesspke-two-boundary-demo/issues), identifying version, observation view, assumptions, expected behavior and actual observations. Use synthetic examples. Do not post reusable private keys, passwords, unrelated private material or unrevealed challenge truth. Functional acceptance and a successful round trip do not prove universal unbreakability.

## Troubleshooting and scope

- Extract the whole ZIP before running; do not run only the EXE copied away from _internal.
- Use fresh output paths. Existing outputs are refused rather than overwritten.
- If Windows reports a sharing error, close programs editing the inputs and retry explicitly.
- Preserve interrupted job directories and use --resume only with unchanged inputs.
- A wrong password, wrong identity or modified bundle must not be treated as successful recovery.
- The demo has two candidates, no signature feature, no GUI. Optional GPU example generation requires the separate source-installation dependencies.

Use this experimental demonstration for inspection with disposable data, not for live cash, valuables or VIP movement instructions.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.4) · [Research hub](https://github.com/waiyip000/TraplessPKE)

Offline-kit resume requires the same acknowledged installation stages and verifies installed bytes. Unacknowledged subprocess attempts are preserved and refused; use a new target explicitly.
