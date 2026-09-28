"""Resumable OWNER walkthrough; ordinary sender/receiver remain separate APIs."""
from contextlib import ExitStack
import importlib.metadata
import os
from pathlib import Path
import time
import uuid

from .files import (DemoError, canonical, compare_files, digest_file, locked_read,
                    read_json, write_json)
from .protocol import send, receive
from .transcript import lease


def _status(path, value):
    temporary = path.with_name(path.name + ".partial-" + uuid.uuid4().hex[:10])
    write_json(temporary, value)
    for attempt in range(8):
        try:
            os.replace(temporary, path)
            break
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(0.1 * (attempt + 1))


def walkthrough(public, private, password, candidates, intended, job, resume=False):
    if type(intended) is not int or intended not in (0, 1) or len(candidates) != 2:
        raise DemoError("Select exactly two candidates and intended index 0 or 1")
    inputs = [Path(p).resolve() for p in [public, private, *candidates]]
    root = Path(job).resolve()
    if any(p == root or p.is_relative_to(root) for p in inputs):
        raise DemoError("Keep original inputs outside the walkthrough job folder")
    if resume:
        if not (root / "REQUEST.json").is_file():
            raise DemoError("No committed request to resume")
    else:
        root.mkdir(parents=True, exist_ok=False)
    with lease(root), ExitStack() as held:
        # Hold every semantic input stable across binding, encrypt, recover and compare.
        for path in dict.fromkeys(inputs):
            held.enter_context(locked_read(path))
        modules = sorted(Path(__file__).parent.glob("*.py"))
        request = {"format": "trapless-demo-walkthrough-1", "classification": "OWNER_PRIVATE",
                   "inputs": [{"path": str(p), "sha256": digest_file(p)} for p in inputs],
                   "intended": intended,
                   "source": {p.name: digest_file(p) for p in modules},
                   "dependencies": {n: importlib.metadata.version(n) for n in ("pqcrypto", "cryptography")}}
        if resume:
            if read_json(root / "REQUEST.json", 1024*1024) != request:
                raise DemoError("Changed input/source/dependency: preserve job and use a versioned migration")
        else:
            write_json(root / "REQUEST.json", request)
        request_digest = digest_file(root / "REQUEST.json")
        status = {"state": "RUNNING", "pid": os.getpid(), "started_unix": time.time(),
                  "classification": "OWNER_PRIVATE", "stages": []}

        def stage(name, action, parent_digest):
            final = root / name
            status["stage"] = name
            _status(root / "status.json", status)
            if final.exists():
                record = read_json(final / "COMMIT.json", 1024*1024)
                if record["request_sha256"] != request_digest or record["parent_sha256"] != parent_digest:
                    raise DemoError("Incompatible stage dependency")
                for rel, expected in record["files"].items():
                    member = (final / rel).resolve()
                    if not member.is_relative_to(final.resolve()) or digest_file(member) != expected:
                        raise DemoError("Checkpoint bytes changed; preserved but refused")
                reused = True
            else:
                temporary = root / (name + ".partial-" + uuid.uuid4().hex[:10])
                temporary.mkdir()
                result = action(temporary)
                files = {p.relative_to(temporary).as_posix(): digest_file(p)
                         for p in temporary.rglob("*") if p.is_file()}
                write_json(temporary / "COMMIT.json", {"request_sha256": request_digest,
                    "parent_sha256": parent_digest, "producer_pid": os.getpid(), "files": files,
                    "result": result, "committed_unix": time.time()})
                os.rename(temporary, final)
                reused = False
            status["stages"].append({"stage": name, "reused": reused})
            return final, digest_file(final / "COMMIT.json")

        try:
            encrypted, first = stage("01-encrypted", lambda f: send(inputs[0], inputs[2:], intended,
                                                                   f / "bundle.tbd"), request_digest)

            def recover(folder):
                result = receive(inputs[1], password, encrypted / "bundle.tbd", folder / "recovered.bin",
                                 folder / "recipient-private.json")
                result["private_recovery_folder"] = Path(result["private_recovery_folder"]).name
                return result

            recovered, second = stage("02-recovered", recover, first)

            def compare(folder):
                comparison = compare_files(inputs[2 + intended], recovered / "recovered.bin")
                write_json(folder / "comparison.json", comparison)
                diagnostic = read_json(recovered / "recipient-private.json")
                if not comparison["equal_bytes"] or diagnostic["recovered_index"] != intended:
                    raise DemoError("Actual private recovery differs from the chosen index/file")
                return comparison

            stage("03-compared", compare, second)
            status.update(state="OWNER_WALKTHROUGH_COMPLETE", finished_unix=time.time(),
                          bundle=str(encrypted / "bundle.tbd"), recovered_file=str(recovered / "recovered.bin"),
                          intended_file=str(inputs[2 + intended]), security_verdict="NOT_ESTABLISHED")
            return status
        except KeyboardInterrupt:
            status.update(state="PAUSED", finished_unix=time.time())
            raise
        except Exception as exc:
            status.update(state="FAILED", error=str(exc), finished_unix=time.time())
            raise
        finally:
            _status(root / "status.json", status)
