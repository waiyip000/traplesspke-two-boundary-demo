"""Local, single-submission blind trial records; no attack engine or live oracle."""
from contextlib import contextmanager
import hashlib
import math
import os
from pathlib import Path
import time
import uuid

from .files import (DemoError, b64, canonical, digest_file, fields, read_json,
                    unb64, write_json)
from .identity import keygen
from .observation import expose
from .protocol import send
from . import records
from .paths import plain, vacant, extended, members
from .protocol import header_read
from .identity import validate_public
from .files import locked_read


@contextmanager
def lease(folder):
    """An OS lock is released if the process exits; the lock carrier may remain."""
    lock = plain(plain(folder) / ".transcript.lock")
    with extended(lock).open("a+b") as f:
        if os.fstat(f.fileno()).st_size == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        if os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise DemoError("Transcript is in use") from exc
            try:
                yield
            finally:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)


def commitment(truth):
    fields(truth, ("trial_id", "bundle_sha256", "index", "nonce"))
    records.hex_id(truth["trial_id"], 32)
    records.hex_id(truth["bundle_sha256"])
    if type(truth["index"]) is not int or truth["index"] not in (0, 1):
        raise DemoError("Invalid truth index")
    unb64(truth["nonce"], 32)
    return hashlib.sha256(b"TraplessPKE-demo/truth-1\x00" + canonical(truth)).hexdigest()


def create(candidates, owner_dir, public_dir, password, view="V1b"):
    owner, public = vacant(owner_dir), vacant(public_dir)
    if owner == public or owner.is_relative_to(public) or public.is_relative_to(owner):
        raise DemoError("Owner and public folders must be separate, not nested")
    if public.exists():
        raise DemoError("Public output already exists")
    owner.mkdir(parents=True, exist_ok=False)
    intended = int.from_bytes(os.urandom(1), "big") & 1
    keygen(owner / "private.json", owner / "public.json", password)
    send(owner / "public.json", candidates, intended, owner / "bundle.tbd")
    trial = uuid.uuid4().hex
    truth = {"trial_id": trial, "bundle_sha256": digest_file(owner / "bundle.tbd"),
             "index": intended, "nonce": b64(os.urandom(32))}
    write_json(owner / "truth.json", truth)
    expose(owner / "private.json", password, owner / "bundle.tbd", public, view)
    view_digest = digest_file(public / "VIEW.json")
    write_json(public / "CHALLENGE.json", {
        "format": "trapless-demo-challenge-1", "trial_id": trial,
        "bundle_sha256": truth["bundle_sha256"], "truth_commitment": commitment(truth),
        "view": view, "view_manifest_sha256": view_digest,
        "state": "OPEN", "random_guess_probability": 0.5,
        "ordering": "Local immutable records; peer exchange required for independent ordering"})
    return {"trial_id": trial, "view": view, "state": "OPEN", "public_dir": str(public)}


def load_challenge(folder):
    folder = plain(folder)
    challenge = read_json(folder / "CHALLENGE.json")
    fields(challenge, ("format", "trial_id", "bundle_sha256", "truth_commitment", "view",
                       "view_manifest_sha256", "state", "random_guess_probability", "ordering"))
    if challenge["format"] != "trapless-demo-challenge-1" or challenge["state"] != "OPEN":
        raise DemoError("Unsupported challenge")
    records.hex_id(challenge["trial_id"], 32)
    for name in ("bundle_sha256", "truth_commitment", "view_manifest_sha256"):
        records.hex_id(challenge[name])
    if challenge["view"] not in ("V0", "V1a", "V1b") or type(challenge["random_guess_probability"]) not in (int, float) or challenge["random_guess_probability"] != 0.5:
        raise DemoError("Unsupported observation model")
    if challenge['ordering']!='Local immutable records; peer exchange required for independent ordering':
        raise DemoError('Invalid local ordering model')
    if challenge["bundle_sha256"] != digest_file(folder / "bundle.tbd"):
        raise DemoError("Changed challenge bundle")
    if challenge["view_manifest_sha256"] != digest_file(folder / "VIEW.json"):
        raise DemoError("Changed observation manifest")
    view = read_json(folder / "VIEW.json")
    fields(view, ("format", "view", "files", "withheld", "scope"))
    if view["format"] != "trapless-demo-view-1" or view["view"] != challenge["view"] or not isinstance(view["files"], dict):
        raise DemoError("Invalid view record")
    names = {"bundle.tbd", "public.json"}
    if view["view"] != "V0":
        names.update(("candidates/candidate-0.bin", "candidates/candidate-1.bin"))
    if view["view"] == "V1b":
        names.add("content-authority.json")
    if set(view["files"]) != names:
        raise DemoError("View members differ from the declared disclosure scope")
    if view['withheld']!=['intent_private_key','intent_shared_secret','sender_choice','selected_output'] or view['scope']!='Explicit exported state; not arbitrary whole-process memory':
        raise DemoError('Invalid declared observation boundary')
    actual=set(members(folder))
    if not actual <= names|{'VIEW.json','CHALLENGE.json','SUBMISSION.json','CLOSED.json','.transcript.lock'}:
        raise DemoError('Undeclared file in public observation folder')
    for name, digest in view["files"].items():
        records.hex_id(digest)
        path = plain(folder / name)
        if not path.is_relative_to(folder.resolve()) or digest_file(path) != digest:
            raise DemoError("Changed observation member")
    public=validate_public(read_json(folder/'public.json'))
    with locked_read(folder/'bundle.tbd') as stream:header_read(stream,public)
    return challenge


def submit(public_dir, prediction, method):
    records.prediction(prediction)
    if not isinstance(method, str) or not 1 <= len(method) <= 4096:
        raise DemoError("Provide a method description of 1–4096 characters")
    folder = Path(public_dir)
    with lease(folder):
        challenge = load_challenge(folder)
        if (folder / "CLOSED.json").exists():
            raise DemoError("Trial has already closed")
        value = {"format": "trapless-demo-submission-2", "trial_id": challenge["trial_id"],
                 "bundle_sha256": challenge["bundle_sha256"], "prediction": prediction,
                 "challenge_sha256": digest_file(folder / "CHALLENGE.json"),
                 "method": method, "recorded_unix": time.time()}
        write_json(folder / "SUBMISSION.json", value)
    return {"state": "SUBMITTED", "answer_disclosed": False,
            "submission_sha256": digest_file(folder / "SUBMISSION.json")}


def close(public_dir, truth_path):
    folder = Path(public_dir)
    with lease(folder):
        challenge = load_challenge(folder)
        submission = read_json(folder / "SUBMISSION.json")
        records.submission(submission, challenge, digest_file(folder / "CHALLENGE.json"))
        truth = read_json(truth_path)
        if commitment(truth) != challenge["truth_commitment"]:
            raise DemoError("Truth commitment mismatch")
        if any(v["trial_id"] != challenge["trial_id"] or
               v["bundle_sha256"] != challenge["bundle_sha256"] for v in (truth, submission)):
            raise DemoError("Trial binding mismatch")
        closed_at = time.time()
        if submission["recorded_unix"] > closed_at:
            raise DemoError("Submission timestamp is after closure; retain it and resolve the clock/order discrepancy")
        guess = submission["prediction"]
        result = {"format": "trapless-demo-closed-2", "trial_id": truth["trial_id"],
                  "state": "TRUTH_REVEALED", "truth": truth,
                  "challenge_sha256": digest_file(folder / "CHALLENGE.json"),
                  "submission_sha256": digest_file(folder / "SUBMISSION.json"),
                  "correct": None if guess is None else guess == truth["index"],
                  "closed_unix": closed_at, "independent_ordering_attested": False}
        write_json(folder / "CLOSED.json", result)
    return result


def summarize(folders):
    seen, correct, answered = set(), 0, 0
    group = None
    for folder in map(Path, folders):
        challenge = load_challenge(folder)
        submission, closed = read_json(folder / "SUBMISSION.json"), read_json(folder / "CLOSED.json")
        records.submission(submission, challenge, digest_file(folder / "CHALLENGE.json"))
        fields(closed, ("format", "trial_id", "state", "truth", "challenge_sha256", "submission_sha256",
                        "correct", "closed_unix", "independent_ordering_attested"))
        if closed["format"] != "trapless-demo-closed-2" or closed["state"] != "TRUTH_REVEALED" or closed["trial_id"] != challenge["trial_id"] or closed["challenge_sha256"] != digest_file(folder / "CHALLENGE.json"):
            raise DemoError("Invalid closed record")
        commitment(closed["truth"])
        if closed["truth"]["trial_id"] != challenge["trial_id"] or closed["truth"]["bundle_sha256"] != challenge["bundle_sha256"]:
            raise DemoError("Closed truth belongs to a different trial")
        records.timestamp(closed["closed_unix"])
        if submission["recorded_unix"] > closed["closed_unix"]:
            raise DemoError("Submission timestamp is after closure")
        if closed["independent_ordering_attested"] is not False:
            raise DemoError("Local records do not attest independent ordering")
        current_group = (challenge["view"], submission["method"])
        if group is not None and group != current_group:
            raise DemoError("Summarize each observation view and method separately")
        group = current_group
        if challenge["trial_id"] in seen:
            raise DemoError("Repeated trial is not a fresh sample")
        seen.add(challenge["trial_id"])
        if commitment(closed["truth"]) != challenge["truth_commitment"] or closed["submission_sha256"] != digest_file(folder / "SUBMISSION.json"):
            raise DemoError("Closed transcript binding mismatch")
        prediction = submission["prediction"]
        actual = None if prediction is None else prediction == closed["truth"]["index"]
        if type(closed["correct"]) is not type(actual) or closed["correct"] != actual:
            raise DemoError("Recorded outcome contradicts the actual prediction and truth")
        if prediction is not None:
            answered += 1
            correct += int(prediction == closed["truth"]["index"])
    n = len(seen)
    value = {"trials": n, "answered": answered, "correct": correct,
             "abstentions": n - answered, "coverage": answered / n if n else 0,
             "claim": "DESCRIPTIVE_ONLY; no registered independent-trial security bound"}
    if answered:
        p = correct / answered
        z = 1.959963984540054
        d = 1 + z*z / answered
        c = (p + z*z / (2*answered)) / d
        h = z * math.sqrt(p*(1-p)/answered + z*z/(4*answered*answered)) / d
        value.update(answered_accuracy=p, wilson95_answered=[c-h, c+h],
                     advantage_upper95_answered=max(abs(c-h-0.5), abs(c+h-0.5)))
    return value


def export_submission(public_dir, destination):
    folder = plain(public_dir)
    destination = vacant(destination)
    if destination.is_relative_to(folder):
        raise DemoError("Export the submission outside the public challenge folder")
    with lease(folder):
        challenge = load_challenge(folder)
        if (folder / "CLOSED.json").exists():
            raise DemoError("Cannot export a prediction as blinded after closure")
        value = records.submission(read_json(folder / "SUBMISSION.json"), challenge,
                                   digest_file(folder / "CHALLENGE.json"))
        write_json(destination, value)
    return {"state": "EXPORTED", "submission_sha256": digest_file(destination), "truth_included": False}


def import_submission(public_dir, source):
    folder = Path(public_dir)
    with lease(folder):
        challenge = load_challenge(folder)
        if (folder / "CLOSED.json").exists():
            raise DemoError("Trial already closed")
        value = records.submission(read_json(source), challenge, digest_file(folder / "CHALLENGE.json"))
        write_json(folder / "SUBMISSION.json", value)
    return {"state": "IMPORTED", "submission_sha256": digest_file(folder / "SUBMISSION.json"),
            "independent_ordering_attested": False}
