"""Streaming two-candidate composition. See PROTOCOL.md for the complete format."""
from collections import deque
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
from pathlib import Path
import struct
import uuid

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pqcrypto.kem import ml_kem_768 as kem

from .files import (DemoError, admit, copy_new, digest_file, exact, output, locked_read,
                    read_json, unb64, write_json)
from .identity import public_id, unlock, validate_public

MAGIC = b"TBDEMO1\x00"
CHUNK = 65536
FRAME = 4 + CHUNK + 16
HEADER_SIZE = 8 + 32 + 16 + kem.CIPHERTEXT_SIZE + 8
TAIL_SIZE = kem.CIPHERTEXT_SIZE + 49 + 16
DOMAIN = b"TraplessPKE-demo-0.1.0/"
MAX_ROUNDS = 2**32 - 1
WORKERS = max(1, min(20, int((os.cpu_count() or 1) * 0.65)))


def derive(secret, bundle_id, label):
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=bundle_id,
                info=DOMAIN + label).derive(secret)


def bounded_map(pool, function, items):
    pending = deque()
    for item in items:
        pending.append(pool.submit(function, item))
        if len(pending) >= 2 * WORKERS:
            yield pending.popleft().result()
    while pending:
        yield pending.popleft().result()


def nonce(slot, ordinal):
    return struct.pack(">IQ", slot, ordinal)


def header_read(f, public):
    header = exact(f, HEADER_SIZE)
    if header[:8] != MAGIC or header[8:40] != public_id(public):
        raise DemoError("Unsupported bundle or recipient mismatch")
    rounds = struct.unpack(">Q", header[-8:])[0]
    if not 1 <= rounds <= MAX_ROUNDS:
        raise DemoError("Invalid bundle frame count")
    expected = HEADER_SIZE + 2 * rounds * FRAME + TAIL_SIZE
    if os.fstat(f.fileno()).st_size != expected:
        raise DemoError("Bundle length does not match its exact grammar")
    return header, header[40:56], header[56:-8], rounds


def send(public_path, candidates, intended, destination):
    if type(intended) is not int or intended not in (0, 1) or len(candidates) != 2:
        raise DemoError("Exactly two candidates and an explicit index 0 or 1 are required")
    public = validate_public(read_json(public_path))
    paths = [Path(p).resolve() for p in candidates]
    with ExitStack() as locks:
        handles = [locks.enter_context(locked_read(p)) for p in paths]
        sizes = [os.fstat(f.fileno()).st_size for f in handles]
        rounds = max(1, (max(sizes) + CHUNK - 1) // CHUNK)
        if rounds > MAX_ROUNDS:
            raise DemoError("File exceeds the published encoding bound")
        required = HEADER_SIZE + 2 * rounds * FRAME + TAIL_SIZE
        admit(destination, required)
        bundle_id = os.urandom(16)
        cc, shared = kem.encrypt(unb64(public["content"], kem.PUBLIC_KEY_SIZE))
        header = MAGIC + public_id(public) + bundle_id + cc + struct.pack(">Q", rounds)
        content_key = derive(shared, bundle_id, b"content")
        binding = hashlib.sha256(DOMAIN + b"binding" + header)
        header_hash = hashlib.sha256(header).digest()
        with output(destination) as target, ThreadPoolExecutor(max_workers=WORKERS) as pool:
            target.write(header)
            for slot, f in enumerate(handles):
                def items():
                    remaining = sizes[slot]
                    for ordinal in range(rounds):
                        size = min(CHUNK, remaining)
                        block = exact(f, size)
                        remaining -= size
                        yield ordinal, struct.pack(">I", size) + block + bytes(CHUNK - size)
                    if f.read(1) or os.fstat(f.fileno()).st_size != sizes[slot]:
                        raise DemoError("Candidate size changed during encryption")

                def encrypt(item):
                    ordinal, clear = item
                    n = nonce(slot, ordinal)
                    return AESGCMSIV(content_key).encrypt(n, clear, header_hash + n)

                for cipher in bounded_map(pool, encrypt, items()):
                    target.write(cipher)
                    binding.update(cipher)
            # The target index first enters cryptographic construction here.
            d = binding.digest()
            ci, intent_secret = kem.encrypt(unb64(public["intent"], kem.PUBLIC_KEY_SIZE))
            intent_key = derive(intent_secret, bundle_id, b"intent/" + d)
            clear = bytes([intended]) + bundle_id + d
            ad = DOMAIN + b"intent-ad" + header_hash + d + ci
            selector = AESGCMSIV(intent_key).encrypt(bytes(12), clear, ad)
            target.write(ci + selector)
        return {"bundle_sha256": digest_file(destination), "bundle_bytes": required,
                "candidate_count": 2, "worker_limit": WORKERS}


def decode_content(public, content_secret, bundle, stage):
    """Actual content-only path. Does not accept an intent key or intended index."""
    stage = Path(stage)
    stage.mkdir(parents=True, exist_ok=False)
    public = validate_public(public)
    paths = [stage / "candidate-0.bin", stage / "candidate-1.bin"]
    with locked_read(bundle) as source:
        header, bundle_id, cc, rounds = header_read(source, public)
        admit(paths[0], 2 * rounds * CHUNK)
        shared = kem.decrypt(content_secret, cc)
        key = derive(shared, bundle_id, b"content")
        header_hash = hashlib.sha256(header).digest()
        binding = hashlib.sha256(DOMAIN + b"binding" + header)
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for slot, path in enumerate(paths):
                short_seen = False

                def items():
                    for ordinal in range(rounds):
                        cipher = exact(source, FRAME)
                        binding.update(cipher)
                        yield ordinal, cipher

                def decrypt(item):
                    ordinal, cipher = item
                    n = nonce(slot, ordinal)
                    try:
                        return AESGCMSIV(key).decrypt(n, cipher, header_hash + n)
                    except InvalidTag as exc:
                        raise DemoError("Bundle authentication failed") from exc

                with output(path) as decoded:
                    for frame in bounded_map(pool, decrypt, items()):
                        count = struct.unpack(">I", frame[:4])[0]
                        if count > CHUNK or (short_seen and count) or any(frame[4 + count:]):
                            raise DemoError("Noncanonical content frame")
                        short_seen = short_seen or count < CHUNK
                        decoded.write(frame[4:4 + count])
        ci = exact(source, kem.CIPHERTEXT_SIZE)
        selector = exact(source, 65)
        if source.read(1):
            raise DemoError("Trailing bundle bytes")
    return {"paths": paths, "binding": binding.digest(), "header_hash": header_hash,
            "bundle_id": bundle_id, "intent_ciphertext": ci, "selector": selector,
            "content_shared_secret": shared, "content_key": key}


def identify(decoded, intent_secret):
    d, bid, ci = decoded["binding"], decoded["bundle_id"], decoded["intent_ciphertext"]
    shared = kem.decrypt(intent_secret, ci)
    key = derive(shared, bid, b"intent/" + d)
    ad = DOMAIN + b"intent-ad" + decoded["header_hash"] + d + ci
    try:
        clear = AESGCMSIV(key).decrypt(bytes(12), decoded["selector"], ad)
    except InvalidTag as exc:
        raise DemoError("Bundle authentication failed") from exc
    if len(clear) != 49 or clear[0] not in (0, 1) or clear[1:17] != bid or clear[17:] != d:
        raise DemoError("Invalid bound selection")
    return clear[0]


def receive(private_path, password, bundle, destination, diagnostic=None):
    public, sc, si = unlock(private_path, password)
    parent = Path(destination).resolve().parent
    admit(destination, 2 * Path(bundle).stat().st_size)
    stage = parent / (".private-recovery-" + uuid.uuid4().hex[:12])
    decoded = decode_content(public, sc, bundle, stage)
    index = identify(decoded, si)
    copy_new(decoded["paths"][index], destination)
    # Ordinary acknowledgements do not publish a selected-only digest or size.
    result = {"state": "RECOVERED", "private_recovery_folder": str(stage)}
    if diagnostic:
        write_json(diagnostic, {"classification": "RECIPIENT_PRIVATE", "recovered_index": index,
                                "candidate_sha256": [digest_file(p) for p in decoded["paths"]]})
    return result
