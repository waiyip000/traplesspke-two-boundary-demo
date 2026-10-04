# Demonstration 0.1.4 — recorded functional correctness

Corrected and functionally validated for its stated demonstration purposes on
the tested Windows x64 / CPython 3.12 environment. This is author-directed
functional validation, not an independent cryptographic security assessment.

The recorded review covers all 17 active Python files and observes all 95 named
functions with separate target-effect checks. All 14 CLI commands were exercised,
with 83 actual terminal invocations and six acceptance families / 81 workers.
These include expected refusal exits and real committed-stage interruption/resume.
Additional controls cover capability consistency, malformed inputs, routing,
checkpoints, installation and actual local directory junction/symbolic-link refusal.
Both optional OpenCL input producers ran with independent all-byte CPU comparisons.
Both 0.1.4 ↔ 0.1.2 wire directions recovered the selected original bytes.

The public [acceptance runner](acceptance.py) supplies six finite control families.
The broader source review and terminal/installer/link controls are separate recorded
work; invoking that runner alone does not reproduce all reported coverage.
Private inputs, keys, passwords, owner truth and runtime directories are excluded.

Final distribution checks retain this tested source and verify the newly assembled
carriers. Release checksums identify exact download bytes. These results do not
establish every branch/input, other platforms, hostile-OS confinement, constant
time or cryptographic security. [Protocol](PROTOCOL.md), [threat model](THREAT_MODEL.md)
and [limitations](LIMITATIONS.md) define the review conditions.
