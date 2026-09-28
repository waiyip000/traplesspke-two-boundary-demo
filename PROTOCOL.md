# Public demo protocol 1 — application version 0.1.2

Application 0.1.2 preserves protocol-1 wire bytes and the `0.1.0` domain separation string.
Source versions and transcript versions are tracked separately; see CHANGES.md.

This is a new Python reference composition of the requested two effects. It is
not wire-compatible with the commercial implementation and inherits no commercial
security result. The complete composition is in `identity.py` and `protocol.py`.

## Primitives and dependency boundary

Suite: `TBDEMO1-MLKEM768-HKDFSHA256-AES256GCMSIV`.

- ML-KEM-768: `pqcrypto==0.3.4`, using its inspectable native primitive bindings.
- AES-256-GCM-SIV, HKDF-SHA256 and scrypt: `cryptography==50.0.1`.
- SHA-256 and operating-system random bytes: Python standard library.
- Optional OpenCL code generates public teaching inputs only. It cannot produce
  keys, encapsulation randomness, selection, plaintext recovery or verdicts.

Use the exact dependency versions in `requirements.txt`. Sources and notices are
listed in `THIRD_PARTY_NOTICES.md`; no private TraplessPKE executable is imported.

## Identity

Independently call ML-KEM key generation twice, producing `(pc,sc)` and `(pi,si)`.
Serialize the public object as JSON with exactly `format`, `suite`, `content`,
`intent`; format is `trapless-demo-public-1`, and key byte strings are canonical
base64. `content=pc`, `intent=pi`. Reject equal content/intent public keys.

Canonical JSON means ASCII, sorted keys, no extra separators/whitespace, no
non-finite values. Duplicate input members and unexpected identity fields are
rejected. `public_id = SHA256(canonical_public_JSON)`.

The private container has exactly `format`, `public`, `salt`, `nonce`, `encrypted`.
Its format is `trapless-demo-private-1`. Draw salt16 and nonce12 independently.
Derive key32 with scrypt(password UTF-8, salt, N=32768, r=8, p=1). Encrypt canonical
JSON `{content:base64(sc), intent:base64(si)}` using AES-GCM-SIV with that nonce and
canonical container metadata excluding `encrypted` as associated data. There are
no variable cost parameters accepted from an untrusted container.

## Binary bundle grammar

All integers are unsigned big-endian. No optional trailing data is admitted.
The two candidate slots preserve the caller's order.

`H = magic8 || public_id32 || bundle_id16 || content_KEM_ciphertext1088 || rounds_u64`

- `magic8 = 54 42 44 45 4d 4f 31 00` (`TBDEMO1` plus NUL).
- `bundle_id` is 16 fresh OS-random bytes.
- Encapsulate to `pc` to obtain `content_KEM_ciphertext` and shared secret `Sc`.
- `C = 65536`; `rounds = max(1, ceil(max(file_sizes)/C))`.
- `1 <= rounds <= 2^32-1`. This is an encoding bound, not a small demonstration
  file-size restriction. Free-space admission may impose a smaller live limit.
- `D = ASCII("TraplessPKE-demo-0.1.0/")`.
- `Kc = HKDF-SHA256(Sc, salt=bundle_id, info=D||"content", length=32)`.

For each slot `s=0,1`, then each ordinal `t=0..rounds-1`:

1. Read up to C bytes remaining in the original file. Set its length to `n`.
2. Construct `F = BE32(n) || bytes_read || zero_bytes(C-n)`.
3. `nonce = BE32(s) || BE64(t)`.
4. `AD = SHA256(H) || nonce`.
5. Append `AES256GCMSIV.Encrypt(Kc, nonce, F, AD)`, exactly 65556 bytes.

Both slots have the same frame count and frame widths, including empty inputs.
No filename, original path or intended index is present in H or content frames.
Frame processing may overlap across CPU workers; emission remains ordered.
The worker ceiling is `max(1, min(20, floor(logical_CPUs * 0.65)))`; this is a
concurrency bound, not a measurement of CPU utilization.

Compute `d = SHA256(D||"binding"||H||all_content_ciphertext_frames)`.
Only after the content body exists does the selected index enter the composition.
Encapsulate independently to `pi`, obtaining `intent_ct1088` and `Si`.

`Ki = HKDF-SHA256(Si, salt=bundle_id, info=D||"intent/"||d, length=32)`.

`I = index_u8 || bundle_id16 || d32`, exactly 49 bytes.

`ADi = D||"intent-ad"||SHA256(H)||d||intent_ct`.

Append `intent_ct || AES256GCMSIV.Encrypt(Ki, zero_nonce12, I, ADi)`.
The selector ciphertext is exactly 65 bytes. The zero selector nonce is used with
a freshly encapsulated and bundle-bound key; normal operation never reuses a
fixed fixture secret. Total bundle size is `HEADER_SIZE + 2*rounds*65556 + 1153`.

## Receiving and exposure

Check the recipient ID, magic, round bound and exact file size before decoding.
Derive Kc through actual decapsulation with sc. Authenticate all frames, reject
invalid lengths/nonzero padding/nonempty frames following a short frame, and
recover both candidate files internally. Recompute d from the consumed ciphertext.
Derive Ki through actual decapsulation with si. Authenticate I and require its
index in `{0,1}`, matching bundle ID and matching d. Only then publish the chosen
candidate to the requested ordinary output path. Receiver inputs never include
sender originals, expected hashes or an expected index.

An explicit content-only exporter uses the same decoder, accepts sc and no si,
and exports both recovered files. V1b additionally exposes actual sc, Sc and Kc.
`recover-content` can independently reconstruct the candidate files from that
authority and bundle. It does not report an intended index.

Private recovery stages retain both plaintext candidates, including on later
intent failure. They are private local working data, never blinded public output.
Ordinary final output is withheld until the full content and intent path succeeds.

## Binding and scope

| Value | Depends on | Public exposure |
|---|---|---|
| pc, pi, public_id | Recipient key generation | V0/V1a/V1b |
| H, frame ciphertexts | Public identity, candidate bytes, fresh content randomness | V0/V1a/V1b |
| d | H and ordered content ciphertext | Publicly derivable |
| intent_ct | pi and fresh intent randomness | V0/V1a/V1b |
| encrypted I | selected index, Si, bundle ID, d | Ciphertext only |
| Candidate bytes/lengths | Actual content decoding | V1a/V1b |
| sc, Sc, Kc | Content capability and actual bundle | V1b |
| si, Si, Ki, selected index, selected output | Private intent/owner/recipient state | Withheld in an open challenge |

Secret-independent content construction is necessary to the intended observation
boundary, but is not a proof of the composed scheme. Independent keys do not
protect intent if a general ML-KEM failure compromises both encapsulations.
AES-GCM-SIV authentication is not sender authentication: anyone with the public
identity can construct a new valid bundle. Signatures are omitted in this profile.

## Publication and failure rules

Outputs use unique partial files, flush and fsync, then non-overwriting publication.
Errors retain partial files; they never imply success. Destination admission uses
actual candidate/bundle sizes and 64 MiB free-space headroom. Windows source handles
deny write/delete sharing while sending; source-size changes are also rejected.
Metadata, bundle decoding and comparison reads use the same stable-read helper.
See Microsoft's [CreateFileW sharing semantics](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

The library has no arbitrary instruction-level resume. The owner `walkthrough`
command commits dependency-bound stages; only
unfinished operations are repeated. Canonical metadata files are bounded to 32 KiB
by ordinary readers; internal bound-job manifests use an explicit 1 MiB bound.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub](https://github.com/waiyip000/TraplessPKE)
