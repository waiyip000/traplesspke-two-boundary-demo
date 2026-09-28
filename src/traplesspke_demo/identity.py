"""Independent ML-KEM-768 capabilities in one password-protected identity."""
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor

from pqcrypto.kem import ml_kem_768 as kem
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .files import DemoError, b64, canonical, fields, read_json, unb64, write_json

SUITE = "TBDEMO1-MLKEM768-HKDFSHA256-AES256GCMSIV"
PUB = "trapless-demo-public-1"
PRIV = "trapless-demo-private-1"


def validate_public(public):
    fields(public, ("format", "suite", "content", "intent"))
    if public["format"] != PUB or public["suite"] != SUITE:
        raise DemoError("Unsupported demo public identity")
    unb64(public["content"], kem.PUBLIC_KEY_SIZE)
    unb64(public["intent"], kem.PUBLIC_KEY_SIZE)
    if public["content"] == public["intent"]:
        raise DemoError("Content and intent identities must differ")
    return public


def public_id(public):
    return hashlib.sha256(canonical(validate_public(public))).digest()


def password_key(password, salt):
    if not isinstance(password, str) or not password:
        raise DemoError("A nonempty private-key password is required")
    return Scrypt(salt=salt, length=32, n=32768, r=8, p=1).derive(password.encode("utf-8"))


def keygen(private_path, public_path, password):
    # Independent RNG-backed keygen calls, not public/content-derived intent.
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(kem.generate_keypair)
        second = pool.submit(kem.generate_keypair)
        pc, sc = first.result()
        pi, si = second.result()
    public = {"format": PUB, "suite": SUITE, "content": b64(pc), "intent": b64(pi)}
    validate_public(public)
    salt, nonce = os.urandom(16), os.urandom(12)
    header = {"format": PRIV, "public": public, "salt": b64(salt), "nonce": b64(nonce)}
    secret = canonical({"content": b64(sc), "intent": b64(si)})
    cipher = AESGCMSIV(password_key(password, salt)).encrypt(nonce, secret, canonical(header))
    write_json(private_path, {**header, "encrypted": b64(cipher)})
    # Public export can be resumed independently if its publication failed.
    write_json(public_path, public)
    return public


def unlock(path, password):
    obj = read_json(path)
    fields(obj, ("format", "public", "salt", "nonce", "encrypted"))
    if obj["format"] != PRIV:
        raise DemoError("Unsupported demo private identity")
    public = validate_public(obj["public"])
    header = {k: v for k, v in obj.items() if k != "encrypted"}
    try:
        raw = AESGCMSIV(password_key(password, unb64(obj["salt"], 16))).decrypt(
            unb64(obj["nonce"], 12), unb64(obj["encrypted"]), canonical(header))
        secret = json.loads(raw)
        fields(secret, ("content", "intent"))
        sc = unb64(secret["content"], kem.SECRET_KEY_SIZE)
        si = unb64(secret["intent"], kem.SECRET_KEY_SIZE)
    except (InvalidTag, ValueError, KeyError) as exc:
        raise DemoError("Private identity authentication failed") from exc
    return public, sc, si


def export_public(private_path, output_path, password):
    public, _, _ = unlock(private_path, password)
    write_json(output_path, public)
    return public
