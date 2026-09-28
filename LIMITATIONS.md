# Limits and acceptance scope

- Exactly two candidates, one suite, unsigned profile, Windows Python 3.12.
- Demo format is intentionally separate from commercial key/bundle formats.
- Both key capabilities use ML-KEM-768. General compromise of that primitive may
  defeat both boundaries; independent key generation does not prevent that.
- Python timing, immutable copies, heap contents and global erasure are unqualified.
- Normal receiving retains private staging plaintext. Access control and cleanup
  of those folders are the owner's responsibility; they are not public exports.
- Windows read handles deny concurrent write/delete while inputs are consumed.
  This does not establish physical-storage integrity or resist a hostile administrator.
- Content exposure intentionally reveals reusable content authority. Only use
  disposable demo identities for exposure/challenge examples.
- Sender authentication/signatures, GUI, vault, account controls and backups are
  outside this initial profile. Bundle authentication is still required.
- Local transcript immutability is not trusted time attestation or isolation from
  a malicious machine owner. No public challenge service is implemented.
- A field export is not an arbitrary process-memory compromise demonstration.
- Functional artifacts, source readability and finite observations are not a
  universal security guarantee. Acceptance and peer review remain distinct.
- Resource ceilings derive from format and free space. A 20-worker maximum is
  a limit, not evidence of 60–70% CPU usage. Small useful GPU work cannot sustain
  60–70% utilization; no dummy load is added and no acceleration gain is claimed.
- Functional acceptance is defined in ACCEPTANCE.md; only actual completed
  controls recorded in the release result count as passed.
- The owner walkthrough resumes committed compatible stages. Separate low-level
  CLI operations preserve partials but do not resume inside a primitive or chunk.
- Demo source uses Apache-2.0 and is [publicly released](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2).
  Research-hub access is separate; this demo does not require that repository.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub — currently private](https://github.com/waiyip000/TraplessPKE)
