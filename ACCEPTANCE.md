# Functional acceptance scope

`acceptance.py` is a sequential local control runner, licensed with the demo.
Run it with the installed offline-kit Python, not a source-path override:

```powershell
& 'D:\TraplessDemo\env\Scripts\python.exe' -I -B .\acceptance.py --work 'D:\DemoControls'
```

Use a new work folder. Use `--resume` only with the same source, primitive versions
and retained control state. Completed families retain commits and are not rerun.
Keep the work folder private: it contains fresh disposable keys, passwords,
owner truth, decoded files and process records. Do not upload that directory.
Published summaries omit these private inputs.

| Family | Consequence checked |
|---|---|
| Runtime/key | Installed package and public export from a new protected identity |
| Selection/reuse | Public-only sending; original-free receiving; both indices; distinct, empty and identical bytes; rename/reorder; reusable key and fresh bundle IDs |
| Authentication | Changed header/frame/selector, truncation, trailing data, wrong key/password reject without final selected output; intact baseline recovers |
| Exposure | Actual V0/V1a/V1b member scope; real decoded candidates; content-only recovery; full-intent positive control |
| Accounting | Submission before reveal; incorrect commitment rejects; import/export; abstention retained; duplicate/late/inconsistent ordering rejects |
| Comparison/resume | Separate real byte reads; changed-byte mismatch; actual process exit after encryption commit; retained commit on resume; failed attempt preserved; output overwrite refused |

The role guard denies ordinary Python opens and production Windows stable-read
calls outside the assigned role/runtime. Actual cryptographic calls are unchanged.
This demonstrates cooperative input separation, not OS confinement against hostile
native code or administrators. The interruption control exits with code 76 just
after actual atomic encryption-stage publication. It is a specific boundary
control, not arbitrary crash or physical power-loss qualification.

Public artifact review separately binds exported members to newly authored demo
source, dependency notices or derived public summaries. Private owner/control runtime material is excluded.

Passing controls does not prove general choice indistinguishability, post-quantum
security, constant-time operation, independent peer ordering, an empirical bound
or absence of every flaw. [VALIDATION.md](VALIDATION.md) summarizes the recorded
0.1.4 functional results. That broader review includes controls beyond the public
acceptance runner; invoking the runner alone does not reproduce every reported
observation. A plan, manifest or launch receipt alone is not a passing result.

Use Python with assertions enabled. Optimized -O/-OO execution is refused before work starts. Checkpoints and retained material are strict bounded JSON; material migration names exactly the five original identity/input files.
