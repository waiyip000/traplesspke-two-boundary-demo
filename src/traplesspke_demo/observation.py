"""Explicit owner export of real decoded content; never exports intent authority."""
from pathlib import Path
import uuid

from .files import (DemoError, b64, copy_new, digest_file, fields, read_json,
                    unb64, write_json)
from .identity import unlock, validate_public
from .protocol import decode_content
from pqcrypto.kem import ml_kem_768 as kem


def expose(private_path, password, bundle, destination, view="V1b"):
    if view not in ("V0", "V1a", "V1b"):
        raise DemoError("View must be V0, V1a or V1b")
    public, sc, _ = unlock(private_path, password)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    copy_new(bundle, destination / "bundle.tbd")
    write_json(destination / "public.json", public)
    members = ["bundle.tbd", "public.json"]
    if view != "V0":
        decoded = decode_content(public, sc, destination / "bundle.tbd", destination / "candidates")
        members += ["candidates/candidate-0.bin", "candidates/candidate-1.bin"]
        if view == "V1b":
            write_json(destination / "content-authority.json", {
                "format": "trapless-demo-content-exposure-1", "public": public,
                "content_private_key": b64(sc),
                "content_shared_secret": b64(decoded["content_shared_secret"]),
                "content_aead_key": b64(decoded["content_key"]),
                "bundle_sha256": digest_file(destination / "bundle.tbd")})
            members.append("content-authority.json")
    write_json(destination / "VIEW.json", {
        "format": "trapless-demo-view-1", "view": view,
        "files": {name: digest_file(destination / name) for name in members},
        "withheld": ["intent_private_key", "intent_shared_secret", "sender_choice", "selected_output"],
        "scope": "Explicit exported state; not arbitrary whole-process memory"})
    return {"view": view, "destination": str(destination), "members": len(members)}


def recover_exposed(exposure_path, bundle, destination):
    obj = read_json(exposure_path)
    fields(obj, ("format", "public", "content_private_key", "content_shared_secret",
                 "content_aead_key", "bundle_sha256"))
    if obj["format"] != "trapless-demo-content-exposure-1" or obj["bundle_sha256"] != digest_file(bundle):
        raise DemoError("Content exposure does not belong to this bundle")
    decoded = decode_content(validate_public(obj["public"]),
                             unb64(obj["content_private_key"], kem.SECRET_KEY_SIZE),
                             bundle, destination)
    return {"recovered_candidates": [str(p) for p in decoded["paths"]],
            "intent_identification": "NOT_PERFORMED_NO_INTENT_CAPABILITY"}
