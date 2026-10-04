# Local development entrypoints

Read `README.md` for customer-independent CLI usage and `PROTOCOL.md` for all
security-relevant composition. Direct dependencies are pinned in requirements.txt.

This demo source is licensed under Apache-2.0. Its explicit export manifest
identifies the files included in the standalone release. Do not publish private runtime data or owner job directories.

Private delivery orchestration is not a runtime dependency. The public installer,
control runner and application functions are included. The source ZIP contains
only the explicit standalone demo members and dependency notices.

Ordinary users do not need that constructor: the public commands perform actual
key generation, selection, encryption, recovery, exposure, submission and reveal.
The separate acceptance runner executes finite functional controls. Consult
ACCEPTANCE.md and the release result for the actual scope; no adversarial campaign
or empirical security bound follows from source construction alone.
