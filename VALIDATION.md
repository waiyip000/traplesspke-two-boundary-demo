# Demo 0.1.2 — Windows functional validation

Completed 28 September 2026, 19:32:28 UTC. Reported by the author-directed project.
This is a sanitized summary of local functional validation, not an independent
peer security assessment.

## Tested artifacts

- Application: **0.1.2**, [release v0.1.2](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2).
- Published source commit: [9b6a448](https://github.com/waiyip000/traplesspke-two-boundary-demo/commit/9b6a448ea540f180fcb4700b73bd3952feb737e0).
- Downloaded Windows executable SHA-256:
  `475480ade950766c99d86d4c667b85efe24bb1427e664f0b2db6d12da4e773a3`.
- Execution used a fresh offline-kit installation, the downloaded Windows
  executable, and the optional published GPU example modules.
- No application-code or executable change was required.

## Recorded outcome

**PASS within the following finite Windows scope.**

| Area | Observed outcome |
| --- | --- |
| Offline installation | Fresh installation, compatible resume and rejection of existing/nested targets |
| Six core families | Identity, selection/reuse, authentication rejection, exposure, transcript accounting, comparison/interruption/resume |
| All fourteen CLI commands | Real terminal password/confirmation handling, command help and functional workflows |
| Candidate recovery | Both selections, empty/identical/reordered inputs, reusable keys, multiple encryption blocks and Unicode/space paths |
| Rejections | Invalid selection, wrong credentials, altered/incomplete bundles, existing output, byte mismatch and invalid transcript order |
| Exchange | Prediction 0, prediction 1, abstention, export/import, reveal, duplicate rejection and aggregate accounting |
| Recovery | Actual termination after a committed encryption stage; compatible resume preserves the commit; changed input rejected |
| Optional GPU examples | Both generators ran on AMD gfx1151; every output byte matched an independent CPU calculation of the public formula; actual encrypted round trips matched |
| Named application functions | 57/57 observed in production calls across the tested Python workflows |
| Invocation totals | 80 terminal commands and 81 core-worker invocations; expected failure exits checked per case |

Commands exercised: `keygen`, `export-public`, `send`, `receive`,
`compare-local`, `expose`, `recover-content`, `challenge-create`, `submit`,
`reveal`, `summarize`, `walkthrough`, `submission-export`, `submission-import`.

## Harness defects and retained results

Two local harness defects stopped intermediate attempts: a receipt filename
collided with an exported test key, and Windows denied replacement of a status
file on the network filesystem. Versioned harness repairs isolated receipts and
added bounded publication retry. The affected export was rerun and compared
successfully. Compatible completed cases were retained. Neither failure required
a demo application change; failed attempts and their exits remain in private
project records.

The public [acceptance runner](acceptance.py), described in [ACCEPTANCE.md](ACCEPTANCE.md),
implements the six core families. The expanded real-terminal driver and
function-call observer were local harnesses and are not included in that runner.
This summary does not claim that invoking acceptance.py alone reproduces all
reported coverage. Private keys, passwords, owner truth, private paths and raw
runtime directories are not published.

## Interpretation

Named-function coverage means a recorded function call, not every code branch or
possible input. Results apply to the tested Windows host and artifact versions.
Other operating systems, fresh source-only installation, arbitrary faults,
sustained CPU/GPU utilization, universal unbreakability and independent blinded
security bounds were not established by this run. See [THREAT_MODEL.md](THREAT_MODEL.md)
and [LIMITATIONS.md](LIMITATIONS.md). The commercial application was outside scope.

The original release acceptance record and release assets remain unchanged.
Main-branch documentation can be corrected separately; see [RELEASE_NOTES.md](RELEASE_NOTES.md).

---

[Demo home](README.md) · [Repository guide](PROJECT_MAP.md) · [Downloads](https://github.com/waiyip000/traplesspke-two-boundary-demo/releases/tag/v0.1.2) · [Research hub](https://github.com/waiyip000/TraplessPKE)
