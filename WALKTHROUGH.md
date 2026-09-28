# Owner walkthrough and recovery

The `walkthrough` command performs genuine encryption, genuine private recovery,
and separate byte comparison in one owner-private workflow. It needs the private
identity because its owner is demonstrating both roles. Ordinary `send` remains
public-key-only; ordinary `receive` never receives the original candidates.

```powershell
python -m traplesspke_demo walkthrough --public public.json --private private.json --candidate first.bmp --candidate second.bmp --intended 1 --job owner-job
```

The intended full path is displayed separately before work. The password is read
privately and is not stored by this command. Completion returns the actual paths
of the bundle and recovered file. Open the recovered BMP in a normal image viewer.
The comparison reads real original/recovered bytes through separate handles.
An explicit recipient-private record also checks the exact index, even when both
candidate byte strings happen to be identical.

The job contains:

1. `REQUEST.json`: source/input/dependency binding, including owner-private choice.
2. `01-encrypted`: committed bundle.
3. `02-recovered`: committed selected output and private recovery material.
4. `03-compared`: actual comparison result.
5. `status.json`: the current owner-private workflow state.

If interrupted, repeat the same command with `--resume`. Completed compatible
stages are consumed; only the unfinished suffix executes. The input files, paths,
chosen index, source modules and primitive versions must match the original request.
Changed bindings or damaged stages are refused. An interrupted partial directory
is preserved and does not count as a checkpoint. No lost original process exit is
invented. This is stage-boundary resume, not instruction-level continuation.

Keep the whole job private. It includes originals' paths/hashes, choice, selected
output, both internally recovered candidates and recipient diagnostics. It is not
a peer challenge export. The peer workflow uses different artifacts and roles.

Windows input handles deny write/delete sharing during encryption and comparison.
The owner walkthrough holds all input handles for the full bound operation. If
another program already holds incompatible write access, admission fails with a
Windows sharing error; close its editing operation and explicitly retry. This does
not claim protection from a malicious administrator or underlying storage failure.

For simple teaching inputs the optional public `example_images.py` producer creates
two distinct viewable BMP candidates with an inspectable OpenCL kernel. It runs
before a challenge bit is selected and does not encode an intended-file marker.
