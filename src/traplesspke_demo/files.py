"""Bounded input and durable, non-overwriting output primitives."""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid


class DemoError(Exception):
    pass


@contextmanager
def locked_read(path):
    """Windows handle denies concurrent write/delete for its entire lifetime."""
    if os.name != "nt":
        raise DemoError("This revision requires Windows read-sharing semantics")
    import ctypes
    import msvcrt
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                  ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    name = str(Path(path).resolve())
    if not name.startswith("\\\\?\\"):
        name = "\\\\?\\UNC\\" + name[2:] if name.startswith("\\\\") else "\\\\?\\" + name
    handle = kernel.CreateFileW(name, 0x80000000, 1, None, 3, 0x08000000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise DemoError(f"Cannot acquire stable read access (Windows error {ctypes.get_last_error()})")
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        kernel.CloseHandle(handle)
        raise
    with os.fdopen(fd, "rb") as stream:
        yield stream


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DemoError("Duplicate JSON member")
        value[key] = item
    return value


def read_json(path, limit=32768):
    with locked_read(path) as f:
        raw = f.read(limit + 1)
    if len(raw) > limit:
        raise DemoError("Metadata encoding limit exceeded")
    try:
        return json.loads(raw, object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(DemoError("Non-finite JSON")))
    except (ValueError, UnicodeError) as exc:
        raise DemoError("Invalid JSON") from exc


def fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise DemoError("Unexpected metadata fields")


def b64(value):
    return base64.b64encode(value).decode("ascii")


def unb64(value, length=None):
    if not isinstance(value, str):
        raise DemoError("Invalid byte encoding")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, UnicodeError) as exc:
        raise DemoError("Invalid byte encoding") from exc
    if b64(raw) != value or (length is not None and len(raw) != length):
        raise DemoError("Noncanonical or wrong-sized byte encoding")
    return raw


def exact(f, count):
    raw = f.read(count)
    if len(raw) != count:
        raise DemoError("Truncated object")
    return raw


def digest_file(path):
    h = hashlib.sha256()
    with locked_read(path) as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def admit(path, required):
    parent = Path(path).resolve().parent
    if not parent.is_dir():
        raise DemoError("Output parent directory does not exist")
    free = shutil.disk_usage(parent).free
    if required + 64 * 1024 * 1024 > free:
        raise DemoError(f"Insufficient destination space: need {required + 64 * 1024 * 1024}, available {free}")


@contextmanager
def output(path):
    path = Path(path).resolve()
    if path.exists():
        raise DemoError("Output already exists; choose a new path")
    temp = path.with_name(path.name + ".partial-" + uuid.uuid4().hex[:12])
    with temp.open("xb") as f:
        yield f
        f.flush()
        os.fsync(f.fileno())
    # Windows rename refuses an existing destination, including a race winner.
    if os.name == "nt":
        os.rename(temp, path)
    else:
        os.link(temp, path)
        temp.unlink()


def write_json(path, value):
    with output(path) as f:
        f.write(canonical(value))


def copy_new(source, target):
    with locked_read(source) as source_file, output(target) as target_file:
        shutil.copyfileobj(source_file, target_file, 1024 * 1024)


def compare_files(original, recovered):
    a, b = Path(original).resolve(), Path(recovered).resolve()
    if a == b or os.path.samefile(a, b):
        raise DemoError("Comparison requires separate original and recovered files")
    total = 0
    ha, hb = hashlib.sha256(), hashlib.sha256()
    equal = True
    with locked_read(a) as left, locked_read(b) as right:
        while True:
            x, y = left.read(65536), right.read(65536)
            ha.update(x)
            hb.update(y)
            equal = equal and x == y
            total += len(x)
            if not x and not y:
                break
    return {"equal_bytes": equal, "original_bytes": total,
            "original_sha256": ha.hexdigest(), "recovered_sha256": hb.hexdigest()}
