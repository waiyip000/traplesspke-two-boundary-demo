"""Install this offline demo kit into an explicitly selected Windows directory."""
import argparse
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import struct
import subprocess
import sys
import uuid
import venv


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    temp = path.with_name(path.name + '.partial-' + uuid.uuid4().hex)
    with temp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if os.name != 'nt' or sys.version_info[:2] != (3, 12) or struct.calcsize('P') != 8:
        raise RuntimeError('Requires Windows x64 CPython 3.12; Python itself is not bundled.')
    kit = Path(__file__).resolve().parent
    manifest = json.loads((kit / 'KIT.json').read_text(encoding='utf-8'))
    for rel, expected in manifest['files'].items():
        source = (kit / rel).resolve()
        if not source.is_relative_to(kit) or digest(source) != expected:
            raise RuntimeError('Kit member differs: ' + rel)
    target = args.target.resolve()
    if target == kit or target.is_relative_to(kit) or kit.is_relative_to(target):
        raise RuntimeError('Choose a dedicated installation outside the kit directory.')
    binding = {'kit_sha256': digest(kit / 'KIT.json'), 'target': str(target),
               'python': sys.version, 'base_python': str(Path(sys.executable).resolve())}
    if target.exists() and not args.resume:
        raise RuntimeError('Target exists; use --resume only for this exact installation.')
    target.mkdir(parents=True, exist_ok=True)
    with (target / '.install.lock').open('a+b') as lock:
        if lock.tell() == 0:
            lock.write(b'0'); lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        request = target / 'INSTALL_REQUEST.json'
        if request.exists():
            if json.loads(request.read_text(encoding='utf-8')) != binding:
                raise RuntimeError('Installation dependency changed; use a new target.')
        else:
            if any(p.name != '.install.lock' for p in target.iterdir()):
                raise RuntimeError('Unbound nonempty target; preserve it and choose a new target.')
            save(request, binding)
        complete = target / 'INSTALL_COMPLETE.json'
        if complete.exists():
            record = json.loads(complete.read_text(encoding='utf-8'))
            if record['binding'] != binding:
                raise RuntimeError('Completion binding differs.')
            print('Retained completed installation:', target)
            return
        environment = target / 'env'
        if not (target / 'ENV_CREATED.json').exists():
            venv.EnvBuilder(with_pip=True, clear=False).create(environment)
            save(target / 'ENV_CREATED.json', {'binding': binding, 'producer_pid': os.getpid()})
        interpreter = environment / 'Scripts/python.exe'
        if not (target / 'PACKAGES_INSTALLED.json').exists():
            with (target / ('pip-' + uuid.uuid4().hex + '.log')).open('x', encoding='utf-8') as log:
                result = subprocess.run([str(interpreter), '-I', '-m', 'pip', '--isolated',
                    'install', '--no-cache-dir', '--no-index', '--find-links', str(kit / 'wheels'),
                    '--require-hashes', '--only-binary=:all:', '--no-compile', '-r',
                    str(kit / 'install.lock')], stdout=log, stderr=subprocess.STDOUT,
                    timeout=1200)
            if result.returncode:
                raise RuntimeError('Offline package installation failed; retain log and explicitly resume.')
            save(target / 'PACKAGES_INSTALLED.json', {'binding': binding, 'pip_exit': result.returncode})
        launcher = target / 'demo.ps1'
        launcher.write_text("$ErrorActionPreference = 'Stop'\n"
            "& (Join-Path $PSScriptRoot 'env\\Scripts\\python.exe') -I -m traplesspke_demo @args\n"
            "exit $LASTEXITCODE\n", encoding='utf-8')
        save(complete, {'state': 'INSTALLED_FROM_OFFLINE_KIT', 'binding': binding,
                       'launcher': str(launcher), 'producer_pid': os.getpid(),
                       'functional_replay': False, 'security_acceptance': 'NOT_ESTABLISHED'})
        print('Installed:', launcher)


if __name__ == '__main__':
    main()
