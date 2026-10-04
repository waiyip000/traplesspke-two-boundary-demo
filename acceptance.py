"""Sequential local functional controls. No attack search or security-bound claim."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import traceback
import uuid


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, obj):
    temporary = path.parent / ('.control-partial-' + uuid.uuid4().hex)
    with temporary.open('x', encoding='utf-8') as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def isolation(role):
    """Input-access controls for these cooperative processes; not an OS sandbox."""
    import ctypes
    roots = [Path(role).resolve(), Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    def permitted(value):
        if isinstance(value, int) or value is None:
            return
        text = os.fsdecode(value)
        if text.upper().startswith('\\\\?\\UNC\\'):
            text = '\\\\' + text[8:]
        elif text.startswith('\\\\?\\'):
            text = text[4:]
        if text.lower() in ('nul', os.devnull.lower()):
            return
        path = Path(text).resolve()
        if not any(path == root or path.is_relative_to(root) for root in roots):
            raise PermissionError('ROLE_INPUT_NOT_AVAILABLE')
    def audit(event, args):
        if event == 'open':
            permitted(args[0])
        if event in ('socket.connect', 'subprocess.Popen', 'os.system'):
            raise PermissionError('EXTERNAL_OPERATION_NOT_AVAILABLE')
    sys.addaudithook(audit)
    original = ctypes.WinDLL
    class GuardedOpen:
        def __init__(self, function):
            object.__setattr__(self, 'function', function)
        def __setattr__(self, name, value):
            setattr(self.function, name, value)
        def __getattr__(self, name):
            return getattr(self.function, name)
        def __call__(self, path, *args):
            permitted(path)
            return self.function(path, *args)
    class Library:
        def __init__(self, library):
            self.library = library
            self.CreateFileW = GuardedOpen(library.CreateFileW)
        def __getattr__(self, name):
            return getattr(self.library, name)
    def load(name, *args, **kwargs):
        library = original(name, *args, **kwargs)
        return Library(library) if str(name).lower() in ('kernel32', 'kernel32.dll') else library
    ctypes.WinDLL = load
    return permitted


def worker():
    request = json.load(sys.stdin)
    role = Path(request['role']).resolve()
    os.chdir(role)
    isolation(role)
    if request.get('control_stop_after_encrypt'):
        rename = os.rename
        def stop_after_commit(source, destination, *args, **kwargs):
            value = rename(source, destination, *args, **kwargs)
            if Path(destination).name == '01-encrypted':
                os._exit(76)  # Actual process exit after real atomic stage publication.
            return value
        os.rename = stop_after_commit
    from traplesspke_demo import files, identity, jobs, observation, protocol, transcript
    import traplesspke_demo
    # The exact installed package, not PYTHONPATH or commercial modules, owns execution.
    origin = Path(traplesspke_demo.__file__).resolve()
    if not origin.is_relative_to(Path(sys.prefix).resolve()):
        raise RuntimeError('Demo was not loaded from the isolated installation')
    calls = {'keygen': identity.keygen, 'export-public': identity.export_public,
             'send': protocol.send, 'receive': protocol.receive, 'compare': files.compare_files,
             'expose': observation.expose, 'recover-content': observation.recover_exposed,
             'challenge': transcript.create, 'submit': transcript.submit, 'reveal': transcript.close,
             'summary': transcript.summarize, 'submission-export': transcript.export_submission,
             'submission-import': transcript.import_submission, 'walkthrough': jobs.walkthrough}
    try:
        action = request['action']
        if action == 'origin':
            result = {'version': traplesspke_demo.__version__, 'origin': str(origin),
                      'isolation': 'Python and published Windows file-read path; not OS confinement'}
        elif action == 'denied-read':
            with files.locked_read(request['args'][0]) as stream:
                stream.read(1)
            raise RuntimeError('Forbidden role read unexpectedly succeeded')
        else:
            result = calls[action](*request.get('args', []), **request.get('kwargs', {}))
        print(json.dumps({'ok': True, 'result': result}))
        return 0
    except Exception as error:
        print(json.dumps({'ok': False, 'error_type': type(error).__name__, 'error': str(error)}))
        return 2


class Controls:
    def __init__(self, root):
        self.root = root
        self.password_path = root / 'owner-password.txt'
        if not self.password_path.exists():
            self.password_path.write_text(secrets.token_urlsafe(32), encoding='ascii')
        self.password = self.password_path.read_text(encoding='ascii')
        self.counter = 0

    def call(self, folder, action, args=(), kwargs=None, fail=False, stop_after_encrypt=False):
        folder.mkdir(parents=True, exist_ok=True)
        self.counter += 1
        request = {'role': str(folder), 'action': action, 'args': list(map(strpath, args)), 'kwargs': kwargs or {}}
        request['control_stop_after_encrypt'] = stop_after_encrypt
        outcome = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--worker'],
            input=json.dumps(request), text=True, capture_output=True, cwd=folder, timeout=120)
        raw = {'action': action, 'returncode': outcome.returncode,
               'stdout': outcome.stdout, 'stderr': outcome.stderr}
        save(folder / ('call-' + uuid.uuid4().hex + '.json'), raw)
        if stop_after_encrypt:
            assert outcome.returncode == 76, raw
            return {'observed_exit': outcome.returncode}
        try:
            result = json.loads(outcome.stdout)
        except ValueError:
            raise RuntimeError('Worker failed before producing a result: ' + outcome.stderr[-1000:])
        if fail:
            assert outcome.returncode == 2 and result['ok'] is False, raw
        else:
            assert outcome.returncode == 0 and result['ok'] is True, raw
        return result

    def keys(self, folder):
        self.call(folder, 'keygen', [folder/'private.json', folder/'public.json', self.password])

    def family(self, name, function):
        folder = self.root / name
        folder.mkdir(exist_ok=True)
        commit = folder / 'COMMIT.json'
        if commit.exists():
            from traplesspke_demo.files import read_json, fields
            previous = read_json(commit, 4*1024**2)
            fields(previous, ("result", "finished", "files"))
            if not isinstance(previous["files"], dict):
                raise RuntimeError("Invalid committed control population")
            from traplesspke_demo.paths import members
            actual=set(members(folder))-{'COMMIT.json'}
            assert actual==set(previous['files']), 'Changed completed control population'
            for rel, expected in previous['files'].items():
                assert sha(folder/rel) == expected, 'Changed completed control'
            return previous['result']
        attempt = folder / ('attempt-' + uuid.uuid4().hex[:8])
        attempt.mkdir()
        save(self.root/'status.json', {'state': 'RUNNING', 'family': name, 'pid': os.getpid()})
        result = function(attempt)
        save(commit, {'result': result, 'finished': time.time(),
                      'files': {p.relative_to(folder).as_posix(): sha(p) for p in folder.rglob('*') if p.is_file()}})
        return result

    def material(self, f):
        migration=self.root/'REUSED_MATERIAL.json'
        if migration.exists():
            from traplesspke_demo.files import read_json, fields
            prior=read_json(migration, 1024**2)
            fields(prior, ("folder", "files"))
            if not isinstance(prior["files"], dict) or set(prior["files"]) != {"private.json","public.json","first.bin","second.bin","empty.bin"}:
                raise RuntimeError("Invalid retained material population")
            origin=Path(prior['folder'])
            for name,expected in prior['files'].items():
                assert sha(origin/name)==expected, 'Changed retained material'
                shutil.copyfile(origin/name,f/name)
        else:
            self.keys(f)
            (f/'first.bin').write_bytes(os.urandom(70003))
            (f/'second.bin').write_bytes(os.urandom(513))
            (f/'empty.bin').write_bytes(b'')
        self.call(f, 'origin')
        self.call(f, 'export-public', [f/'private.json', f/'exported.json', self.password])
        assert (f/'public.json').read_bytes() == (f/'exported.json').read_bytes()
        return {'folder': str(f), 'key_export': 'PASS', 'A01_runtime': 'ISOLATED_INSTALLED_PACKAGE'}

    def functional(self, f, material):
        m = Path(material['folder'])
        cases = [('distinct-0', 'first.bin', 'second.bin', 0), ('distinct-1', 'first.bin', 'second.bin', 1),
                 ('empty-0', 'empty.bin', 'second.bin', 0), ('empty-1', 'first.bin', 'empty.bin', 1),
                 ('identical-0', 'first.bin', 'first.bin', 0), ('identical-1', 'first.bin', 'first.bin', 1),
                 ('reordered-renamed', 'second.bin', 'first.bin', 1),
                 ('repeated-fresh', 'first.bin', 'second.bin', 0)]
        results, random_ids, hashes = [], [], []
        for label, a, b, index in cases:
            sender, receiver = f/label/'sender', f/label/'receiver'
            sender.mkdir(parents=True); receiver.mkdir()
            for origin, dest in [(m/'public.json', sender/'public.json'), (m/a, sender/'renamed-A.data'),
                                 (m/b, sender/'renamed-B.data'), (m/'private.json', receiver/'private.json')]:
                shutil.copyfile(origin, dest)
            self.call(sender, 'denied-read', [receiver/'private.json'], fail=True)
            self.call(sender, 'send', [sender/'public.json', [str(sender/'renamed-A.data'),str(sender/'renamed-B.data')], index, sender/'bundle.tbd'])
            shutil.copyfile(sender/'bundle.tbd', receiver/'bundle.tbd')
            self.call(receiver, 'denied-read', [sender/'renamed-A.data'], fail=True)
            received = self.call(receiver, 'receive', [receiver/'private.json', self.password,
                receiver/'bundle.tbd', receiver/'selected.bin', receiver/'diagnostic.json'])
            diagnostic = json.loads((receiver/'diagnostic.json').read_text())
            expected = sender/('renamed-A.data' if index == 0 else 'renamed-B.data')
            assert expected.read_bytes() == (receiver/'selected.bin').read_bytes()
            assert diagnostic['recovered_index'] == index
            recovery = Path(received['result']['private_recovery_folder'])
            for slot, original in enumerate([sender/'renamed-A.data', sender/'renamed-B.data']):
                assert original.read_bytes() == (recovery/f'candidate-{slot}.bin').read_bytes()
            with (sender/'bundle.tbd').open('rb') as stream:
                header = stream.read(1152)
            random_ids.append(header[40:56].hex()); hashes.append(sha(sender/'bundle.tbd'))
            results.append({'case': label, 'index': diagnostic['recovered_index'], 'bytes': expected.stat().st_size})
        assert len(set(random_ids)) == len(cases) and len(set(hashes)) == len(cases)
        return {'A02': 'PASS', 'A03': 'PASS', 'A04': 'PASS', 'A05': 'PASS', 'A06': 'PASS',
                'cases': results, 'folder': str(f), 'fresh_bundle_ids': random_ids,
                'ceiling': 'Finite functional controls; randomness uniqueness is not an RNG proof'}

    def authentication(self, f, material, functional):
        m = Path(material['folder']); original = Path(functional['folder'])/'distinct-0/sender/bundle.tbd'
        shutil.copyfile(m/'private.json', f/'private.json')
        raw = original.read_bytes()
        variations = {'changed-header': (40, 1), 'changed-frame': (1152+10, 1),
                      'changed-selector': (len(raw)-1, 1)}
        for label, (offset, mask) in variations.items():
            changed = bytearray(raw); changed[offset] ^= mask
            (f/(label+'.tbd')).write_bytes(changed)
        (f/'truncated.tbd').write_bytes(raw[:-1])
        (f/'trailing.tbd').write_bytes(raw+b'0')
        self.keys(f/'wrong-key')
        shutil.copyfile(original, f/'baseline.tbd')
        outcomes = []
        for label in [*variations, 'truncated', 'trailing', 'wrong-key', 'wrong-password']:
            key = f/'wrong-key/private.json' if label == 'wrong-key' else f/'private.json'
            bundle = f/(label+'.tbd') if label not in ('wrong-key','wrong-password') else f/'baseline.tbd'
            password = self.password+'wrong' if label == 'wrong-password' else self.password
            result = self.call(f, 'receive', [key, password, bundle, f/(label+'.out')], fail=True)
            assert result['error_type'] == 'DemoError', result
            assert not (f/(label+'.out')).exists()
            outcomes.append({'case': label, 'rejection': result['error']})
        self.call(f, 'receive', [f/'private.json', self.password, f/'baseline.tbd', f/'restored.out'])
        assert (f/'restored.out').read_bytes() == (m/'first.bin').read_bytes()
        return {'A07': 'PASS', 'outcomes': outcomes, 'baseline_restored': True,
                'private_partial_plaintext': 'May remain; no final selected output on rejected bundles'}

    def exposure(self, f, material, functional):
        m = Path(material['folder'])
        shutil.copyfile(m/'private.json', f/'private.json')
        shutil.copyfile(Path(functional['folder'])/'distinct-1/sender/bundle.tbd', f/'bundle.tbd')
        views = []
        for view in ('V0','V1a','V1b'):
            self.call(f, 'expose', [f/'private.json', self.password, f/'bundle.tbd', f/view, view])
            manifest = json.loads((f/view/'VIEW.json').read_text())
            expected = {'public.json','bundle.tbd'}
            if view != 'V0':
                expected |= {'candidates/candidate-0.bin','candidates/candidate-1.bin'}
                for slot, name in enumerate(('first.bin','second.bin')):
                    assert (f/view/f'candidates/candidate-{slot}.bin').read_bytes() == (m/name).read_bytes()
            if view == 'V1b': expected.add('content-authority.json')
            actual = {p.relative_to(f/view).as_posix() for p in (f/view).rglob('*') if p.is_file()}
            assert set(manifest['files']) == expected and actual == expected|{'VIEW.json'}
            views.append({'view': view, 'members': sorted(actual)})
        role = f/'content-only'; role.mkdir()
        shutil.copyfile(f/'V1b/content-authority.json', role/'authority.json')
        shutil.copyfile(f/'bundle.tbd', role/'bundle.tbd')
        self.call(role, 'denied-read', [f/'private.json'], fail=True)
        self.call(role, 'recover-content', [role/'authority.json', role/'bundle.tbd', role/'decoded'])
        for slot, name in enumerate(('first.bin','second.bin')):
            assert (role/f'decoded/candidate-{slot}.bin').read_bytes() == (m/name).read_bytes()
        authority = json.loads((role/'authority.json').read_text())
        assert set(authority) == {'format','public','content_private_key','content_shared_secret','content_aead_key','bundle_sha256'}
        self.call(f, 'receive', [f/'private.json', self.password, f/'bundle.tbd', f/'full-control.out', f/'full-control.json'])
        assert json.loads((f/'full-control.json').read_text())['recovered_index'] == 1
        return {'A08':'PASS', 'A09':'PASS_SCOPED_CAPABILITY_CONTROL', 'A10':'PASS_EXPLICIT_SERIALIZED_VIEW',
                'views':views, 'claim':'No general indistinguishability, memory or timing claim'}

    def accounting(self, f, material):
        m = Path(material['folder'])
        for name in ('first.bin','second.bin'): shutil.copyfile(m/name, f/name)
        cases = []
        for label, prediction in [('guess',0),('abstain',None)]:
            owner, peer = f/(label+'-owner'), f/(label+'-public')
            self.call(f, 'challenge', [[str(f/'first.bin'),str(f/'second.bin')], owner, peer, self.password, 'V1b'])
            # Real ordering, deliberately a labelled local control rather than independent peer evidence.
            self.call(f, 'reveal', [peer, owner/'truth.json'], fail=True)
            self.call(f, 'submit', [peer, prediction, 'LOCAL_FUNCTIONAL_CONTROL_NOT_SECURITY_EVIDENCE'])
            assert not (peer/'CLOSED.json').exists()
            self.call(f, 'submission-export', [peer, f/(label+'-submission.json')])
            imported = f/(label+'-import'); imported.mkdir()
            for path in peer.rglob('*'):
                if path.is_file() and path.name not in ('SUBMISSION.json','.transcript.lock'):
                    target = imported/path.relative_to(peer); target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path,target)
            self.call(f, 'submission-import', [imported, f/(label+'-submission.json')])
            truth = json.loads((owner/'truth.json').read_text())
            damaged = dict(truth); damaged['index'] = 1-truth['index']
            save(f/(label+'-wrong-truth.json'), damaged)
            self.call(f, 'reveal', [imported, f/(label+'-wrong-truth.json')], fail=True)
            assert not (imported/'CLOSED.json').exists()
            self.call(f, 'reveal', [imported, owner/'truth.json'])
            summary = self.call(f, 'summary', [[str(imported)]])['result']
            assert summary['answered'] == (prediction is not None)
            assert summary['abstentions'] == (prediction is None)
            assert summary['correct'] == (int(prediction == truth['index']) if prediction is not None else 0)
            self.call(f, 'submit', [imported, 1, 'late'], fail=True)
            self.call(f, 'summary', [[str(imported),str(imported)]], fail=True)
            closed_path = imported/'CLOSED.json'
            original = closed_path.read_bytes(); changed = json.loads(original)
            changed['closed_unix'] = 0
            save(closed_path, changed)
            self.call(f, 'summary', [[str(imported)]], fail=True)
            closed_path.write_bytes(original)
            self.call(f, 'summary', [[str(imported)]])
            cases.append({'kind':label, 'summary':summary})
        return {'A11':'PASS_LOCAL_ACCOUNTING_CONTROLS', 'independent_peer_evidence':False, 'cases':cases}

    def comparison_resume(self, f, material):
        m = Path(material['folder'])
        for name in ('first.bin','second.bin','private.json','public.json'):
            shutil.copyfile(m/name,f/name)
        shutil.copyfile(f/'first.bin',f/'actual-copy.bin')
        assert self.call(f,'compare',[f/'first.bin',f/'actual-copy.bin'])['result']['equal_bytes']
        raw = bytearray((f/'actual-copy.bin').read_bytes()); raw[3] ^= 1
        (f/'changed.bin').write_bytes(raw)
        assert self.call(f,'compare',[f/'first.bin',f/'changed.bin'])['result']['equal_bytes'] is False
        self.call(f,'compare',[f/'first.bin',f/'first.bin'],fail=True)
        args = [f/'public.json', f/'private.json', self.password, [str(f/'first.bin'),str(f/'second.bin')], 1, f/'job']
        interrupted = self.call(f,'walkthrough',args,stop_after_encrypt=True)
        # Also retain a real private-key authentication failure on explicit resume.
        bad = list(args); bad[2] += '-wrong'
        self.call(f,'walkthrough',bad,kwargs={'resume':True},fail=True)
        first_commit = sha(f/'job/01-encrypted/COMMIT.json')
        first_bundle = sha(f/'job/01-encrypted/bundle.tbd')
        assert not (f/'job/02-recovered').exists()
        failures = sorted(p.name for p in (f/'job').glob('02-recovered.partial-*'))
        assert failures
        result = self.call(f,'walkthrough',args,kwargs={'resume':True})['result']
        assert result['stages'][0]['reused'] is True
        assert sha(f/'job/01-encrypted/COMMIT.json') == first_commit
        assert sha(f/'job/01-encrypted/bundle.tbd') == first_bundle
        assert all((f/'job'/name).exists() for name in failures)
        assert (f/'job/02-recovered/recovered.bin').read_bytes() == (f/'second.bin').read_bytes()
        # Non-overwriting admission preserves an already published ordinary output.
        before = sha(f/'job/02-recovered/recovered.bin')
        self.call(f,'receive',[f/'private.json',self.password,f/'job/01-encrypted/bundle.tbd',f/'job/02-recovered/recovered.bin'],fail=True)
        assert sha(f/'job/02-recovered/recovered.bin') == before
        return {'A12':'PASS','A13':'PASS_COMMITTED_STAGE_INTERRUPTION_AND_RESUME',
                'preserved_encrypted_commit':first_commit, 'retained_failed_stages':failures,
                'actual_interruption_exit':interrupted['observed_exit'],
                'arbitrary_instruction_crash':'NOT_TESTED'}


def strpath(value):
    return str(value) if isinstance(value,Path) else value


def main():
    if not __debug__:
        raise RuntimeError("Functional controls require assertions enabled; do not use -O")
    from traplesspke_demo.files import read_json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--work',type=Path)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.worker: return worker()
    if args.work is None: parser.error('--work is required')
    root=args.work.resolve()
    if root.exists() and not args.resume: raise RuntimeError('Use a new work directory or explicit --resume')
    root.mkdir(parents=True,exist_ok=True)
    import importlib.metadata
    import traplesspke_demo
    binding={'harness':sha(__file__), 'modules':{p.name:sha(p) for p in Path(traplesspke_demo.__file__).parent.glob('*.py')},
             'dependencies':{n:importlib.metadata.version(n) for n in ('pqcrypto','cryptography')}}
    if (root/'REUSED_MATERIAL.json').exists():
        binding['retained_material']=sha(root/'REUSED_MATERIAL.json')
    from traplesspke_demo.transcript import lease
    with lease(root):
        bound=root/'BINDING.json'
        if bound.exists(): assert read_json(bound, 1024**2) == binding,'Changed acceptance binding'
        else: save(bound,binding)
        controls=Controls(root)
        try:
            material=controls.family('01-runtime-key',controls.material)
            functional=controls.family('02-selection-reuse',lambda f:controls.functional(f,material))
            authentication=controls.family('03-authentication',lambda f:controls.authentication(f,material,functional))
            exposure=controls.family('04-exposure',lambda f:controls.exposure(f,material,functional))
            accounting=controls.family('05-accounting',lambda f:controls.accounting(f,material))
            resume=controls.family('06-comparison-resume',lambda f:controls.comparison_resume(f,material))
            report={'state':'FUNCTIONAL_CONTROLS_COMPLETE','finished':time.time(), 'binding':binding,
                    'runtime':material,'functional':functional,'authentication':authentication,
                    'exposure':exposure,'accounting':accounting,'comparison_resume':resume,
                    'A14':'SEPARATE_EXPORT_REVIEW','security_bound':'NOT_ESTABLISHED'}
            
            if (root/'REPORT.json').exists():
                assert read_json(root/'REPORT.json', 4*1024**2)['binding']==binding
                save(root/('REUSE-'+uuid.uuid4().hex+'.json'),{'state':'COMMITTED_FAMILIES_REUSED','new_worker_calls':controls.counter})
            else:save(root/'REPORT.json',report)
            save(root/'status.json',{'state':report['state'],'pid':os.getpid()})
        except BaseException as error:
            save(root/'status.json',{'state':'FAILED','error':str(error),'pid':os.getpid()})
            raise
    return 0


if __name__=='__main__':
    sys.exit(main())
