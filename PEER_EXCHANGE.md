# Exchange a prediction without exchanging private state

The owner sends the reviewer only the allowlisted public view and complete demo
source. The reviewer keeps a separate local copy. No user private key, owner job,
open truth record or selected plaintext belongs in that transfer.

After inspecting a trial, the reviewer records a prediction or abstention:

```powershell
python -m traplesspke_demo submit --public-dir reviewer-copy --prediction abstain --method "No conclusion from the supplied content-exposed view"
python -m traplesspke_demo submission-export --public-dir reviewer-copy --out prediction.json
```

Send only `prediction.json` back to the owner. It binds the original challenge
bytes, trial ID, bundle digest, method and prediction. The owner imports it into
the original public directory before closing the trial:

```powershell
python -m traplesspke_demo submission-import --public-dir owner-public --input prediction.json
python -m traplesspke_demo reveal --public-dir owner-public --truth owner-private/truth.json
```

Only one submission is accepted. Import/export never reports correctness. A closed
trial cannot accept a new submission or export an existing prediction as blinded.
The owner then sends `CLOSED.json` alongside the original challenge and recorded
submission, so the reviewer can inspect the committed truth and score the closed
record. No private key is needed to read a closed result.

The closure does not establish independent timing. The participants must make the
exchange order observable outside the owner's editable filesystem. Local clocks,
immutable-file conventions and a self-authored receipt are not an independent
timestamping authority. Do not count a teaching transcript as peer evidence.

The source rejects out-of-schema submissions, floating-point or boolean guesses,
changed trial bindings, contradictory stored results and duplicate trial IDs.
Summary rows must share the same observation view and declared method. Abstentions
remain visible; reported intervals are descriptive and are not a security gate.

The application reads challenge/view grammar version 1. New submissions and
closures use record version 2. Earlier submitted or closed records are not
silently relabelled. Contradictory submission/closure timestamps are rejected;
resolve a clock discrepancy without modifying an already exchanged prediction.

Submission export must be outside the public challenge folder. Extra files invalidate its declared observation population.
