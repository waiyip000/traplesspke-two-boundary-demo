# Observation model

The hypothesis under inspection is computational sender-choice privacy under
explicit content disclosure, while the intent capability remains secret.

| View | Delivered data |
|---|---|
| V0 | Public identity, bundle, full demo source and public protocol |
| V1a | V0 plus both files recovered by the actual content decoder |
| V1b | V1a plus sc, the actual content shared secret and content AEAD key |
| Recipient | Full private identity and bundle; can recover intended file |
| Full compromise | Content and intent private capabilities; no hidden-choice claim |

The public code discloses every TraplessPKE-specific operation. Secrecy rests on
generated keys and stated primitive/composition assumptions, not hidden code.
Source disclosure permits independent reimplementation of this demonstration.

A content exposure is an explicit serializable state, not a whole-process dump.
The owner process also holds intent and truth. Python objects, swap, crash dumps,
administrative access, shared-folder permissions and endpoint malware are not
isolated by these role labels. Give peers only the public view directory.

V1b intentionally exposes one key capability, but does not demonstrate survival
of an arbitrary algorithmic break of ML-KEM. Both capabilities use ML-KEM-768;
a general break affecting both paths would invalidate the intended boundary.

Decoy meaning, unequal prior plausibility, sender leaks and later recipient actions
can reveal intent. The basic challenge chooses its bit uniformly after fixing the
candidate pair. Its 1/2 guessing baseline applies to that procedure, not every
real-world message choice.

Public metadata includes suite, recipient identity, two slots and padded maximum
length. Fixed widths avoid an intentional index marker; timing/allocator/OS side
channels have not been qualified. No constant-time Python, global erasure,
universal secrecy or post-quantum security verdict is asserted.

The system has no remote receiver or hypothesis-confirmation endpoint. Local
challenge submission records one prediction before closure and returns no truth.
Owner truth is revealed only by a separate close operation. A hostile owner of
the filesystem can rewrite local history: external peer exchange is necessary
to attest genuine submission ordering. Teaching runs on one PC are not blinded
peer evidence. A revealed trial cannot be reused as a fresh trial.

See the [complete protocol](PROTOCOL.md), [peer-exchange procedure](PEER_EXCHANGE.md) and [functional-validation limits](VALIDATION.md). The [repository guide](PROJECT_MAP.md) distinguishes this demo from the research record and commercial application.

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub — currently private](https://github.com/waiyip000/TraplessPKE)
