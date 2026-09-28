"""Customer-independent local CLI; all commands call the published core."""
import argparse
import getpass
import json
from pathlib import Path
import sys

from . import __version__
from .files import DemoError, compare_files
from .identity import export_public, keygen
from .observation import expose, recover_exposed
from .protocol import receive, send
from . import transcript
from .jobs import walkthrough


def password(new=False):
    value = getpass.getpass("Private identity password: ")
    if new and getpass.getpass("Repeat password: ") != value:
        raise DemoError("Passwords do not match")
    return value


def parser():
    p = argparse.ArgumentParser(description="TraplessPKE inspectable two-candidate demonstration")
    p.add_argument("--version", action="version", version=__version__)
    commands = p.add_subparsers(dest="command", required=True)
    key = commands.add_parser("keygen")
    key.add_argument("--private", required=True)
    key.add_argument("--public", required=True)
    export = commands.add_parser("export-public")
    export.add_argument("--private", required=True)
    export.add_argument("--out", required=True)
    enc = commands.add_parser("send")
    enc.add_argument("--public", required=True)
    enc.add_argument("--candidate", action="append", required=True)
    enc.add_argument("--intended", type=int, choices=[0, 1], required=True)
    enc.add_argument("--out", required=True)
    enc.add_argument("--yes", action="store_true", help="Skip sender-local path confirmation")
    dec = commands.add_parser("receive")
    dec.add_argument("--private", required=True)
    dec.add_argument("--bundle", required=True)
    dec.add_argument("--out", required=True)
    dec.add_argument("--private-diagnostic")
    cmp = commands.add_parser("compare-local")
    cmp.add_argument("original")
    cmp.add_argument("recovered")
    obs = commands.add_parser("expose")
    obs.add_argument("--private", required=True)
    obs.add_argument("--bundle", required=True)
    obs.add_argument("--out", required=True)
    obs.add_argument("--view", choices=["V0", "V1a", "V1b"], default="V1b")
    rec = commands.add_parser("recover-content")
    rec.add_argument("--authority", required=True)
    rec.add_argument("--bundle", required=True)
    rec.add_argument("--out", required=True)
    challenge = commands.add_parser("challenge-create")
    challenge.add_argument("--candidate", action="append", required=True)
    challenge.add_argument("--owner-dir", required=True)
    challenge.add_argument("--public-dir", required=True)
    challenge.add_argument("--view", choices=["V0", "V1a", "V1b"], default="V1b")
    sub = commands.add_parser("submit")
    sub.add_argument("--public-dir", required=True)
    sub.add_argument("--prediction", choices=["0", "1", "abstain"], required=True)
    sub.add_argument("--method", required=True)
    close = commands.add_parser("reveal")
    close.add_argument("--public-dir", required=True)
    close.add_argument("--truth", required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("folders", nargs="+")
    walk = commands.add_parser("walkthrough", help="Owner-only encrypt/recover/compare with stage resume")
    walk.add_argument("--public", required=True)
    walk.add_argument("--private", required=True)
    walk.add_argument("--candidate", action="append", required=True)
    walk.add_argument("--intended", type=int, choices=[0, 1], required=True)
    walk.add_argument("--job", required=True)
    walk.add_argument("--resume", action="store_true")
    walk.add_argument("--yes", action="store_true")
    ex = commands.add_parser("submission-export")
    ex.add_argument("--public-dir", required=True)
    ex.add_argument("--out", required=True)
    im = commands.add_parser("submission-import")
    im.add_argument("--public-dir", required=True)
    im.add_argument("--input", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "keygen":
            keygen(args.private, args.public, password(True))
            result = {"state": "CREATED", "public": args.public, "private": args.private}
        elif args.command == "export-public":
            export_public(args.private, args.out, password())
            result = {"state": "EXPORTED", "out": args.out}
        elif args.command == "send":
            if len(args.candidate) != 2:
                raise DemoError("Exactly two --candidate arguments are required")
            print("Sender-private intended file:", Path(args.candidate[args.intended]).resolve(), file=sys.stderr)
            if not args.yes and input("Encrypt this selection? Type yes: ").strip() != "yes":
                raise DemoError("Cancelled before encryption")
            result = send(args.public, args.candidate, args.intended, args.out)
        elif args.command == "receive":
            result = receive(args.private, password(), args.bundle, args.out, args.private_diagnostic)
        elif args.command == "compare-local":
            result = compare_files(args.original, args.recovered)
            print(json.dumps(result, indent=2))
            return 0 if result["equal_bytes"] else 1
        elif args.command == "expose":
            result = expose(args.private, password(), args.bundle, args.out, args.view)
        elif args.command == "recover-content":
            result = recover_exposed(args.authority, args.bundle, args.out)
        elif args.command == "challenge-create":
            result = transcript.create(args.candidate, args.owner_dir, args.public_dir, password(True), args.view)
        elif args.command == "submit":
            prediction = None if args.prediction == "abstain" else int(args.prediction)
            result = transcript.submit(args.public_dir, prediction, args.method)
        elif args.command == "walkthrough":
            if len(args.candidate) != 2:
                raise DemoError("Exactly two --candidate arguments are required")
            print("Owner-private intended file:", Path(args.candidate[args.intended]).resolve(), file=sys.stderr)
            if not args.yes and input("Run owner encrypt/recover/compare? Type yes: ").strip() != "yes":
                raise DemoError("Cancelled before walkthrough")
            result = walkthrough(args.public, args.private, password(), args.candidate,
                                 args.intended, args.job, args.resume)
        elif args.command == "submission-export":
            result = transcript.export_submission(args.public_dir, args.out)
        elif args.command == "submission-import":
            result = transcript.import_submission(args.public_dir, args.input)
        elif args.command == "reveal":
            result = transcript.close(args.public_dir, args.truth)
        else:
            result = transcript.summarize(args.folders)
        print(json.dumps(result, indent=2))
        return 0
    except (DemoError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"state": "FAILED", "error": str(exc)}), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted; partial files retained, no success asserted.", file=sys.stderr)
        return 130
