"""Bounded offline Windows installation; verified resume, no blind process replay."""
import argparse,hashlib,json,msvcrt,os,struct,subprocess,sys,uuid,venv,zipfile
from pathlib import Path

def pairs(items):
    result={}
    for key,value in items:
        if key in result:raise RuntimeError('Duplicate installation metadata member')
        result[key]=value
    return result

def read(path):
    with Path(path).open('rb') as stream:raw=stream.read(4*1024**2+1)
    if len(raw)>4*1024**2:raise RuntimeError('Installation metadata limit exceeded')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(RuntimeError('Non-finite metadata')))

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def safe(path):
    path=Path(path).absolute()
    reserved={'CON','AUX','PRN','NUL','CONIN$','CONOUT$',*(f'COM{i}' for i in '123456789\u00b9\u00b2\u00b3'),*(f'LPT{i}' for i in '123456789\u00b9\u00b2\u00b3')}
    if str(path).startswith(('\\\\?\\','\\\\.\\')):raise RuntimeError('Device namespace refused')
    for name in path.parts[1:]:
        if name in ('.','..'):continue
        if name.endswith((' ','.')) or name.split('.')[0].rstrip(' .').upper() in reserved or any(ord(c)<32 or c in ':<>"|?*' for c in name):raise RuntimeError('Unsafe installation path')
    for item in (path,*path.parents):
        try:info=item.lstat()
        except FileNotFoundError:continue
        if getattr(info,'st_file_attributes',0)&0x400:raise RuntimeError('Reparse installation route refused')
    return path.resolve()

def save(path,value):
    path=safe(path);temp=path.parent/('.install-partial-'+uuid.uuid4().hex)
    with temp.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.flush();os.fsync(stream.fileno())
    os.replace(safe(temp),safe(path))

def check_kit(kit):
    kit=safe(kit);manifest=read(kit/'KIT.json')
    if set(manifest)!={'application_version','source_license','files'} or manifest['application_version']!='0.1.4' or manifest['source_license']!='Apache-2.0' or not isinstance(manifest['files'],dict):raise RuntimeError('Wrong kit authority')
    names=manifest['files']
    if len(names)!=len({n.casefold() for n in names}):raise RuntimeError('Case-colliding kit members')
    actual=set()
    for item in kit.rglob('*'):
        safe(item)
        if item.is_file():actual.add(item.relative_to(kit).as_posix())
    if actual!=set(names)|{'KIT.json'}:raise RuntimeError('Unmapped kit member')
    for rel,expected in names.items():
        if not isinstance(rel,str) or '\\' in rel or ':' in rel or rel.startswith('/') or any(x in ('','.','..') for x in rel.split('/')):raise RuntimeError('Unsafe kit member')
        source=safe(kit/rel)
        if not source.is_relative_to(kit) or digest(source)!=expected:raise RuntimeError('Kit member differs: '+rel)
    return manifest

def verify_install(kit,target,manifest):
    """Derive expected installed payloads from the exact pinned wheel bytes."""
    payloads={}
    for wheel in sorted((kit/'wheels').glob('*.whl')):
        with zipfile.ZipFile(wheel) as archive:
            if len(archive.namelist())!=len({n.casefold() for n in archive.namelist()}):raise RuntimeError('Duplicate or case-colliding wheel member')
            for name in archive.namelist():
                if name.endswith('/') or name.endswith('.dist-info/RECORD'):continue
                if name.startswith('/') or '\\' in name or ':' in name or any(x in ('','.','..') for x in name.split('/')) or '.data' in name.split('/')[0]:raise RuntimeError('Unsupported wheel routing')
                dest=safe(target/'env/Lib/site-packages'/name)
                expected=hashlib.sha256(archive.read(name)).hexdigest()
                if digest(dest)!=expected:raise RuntimeError('Installed wheel payload changed: '+name)
                rel=dest.relative_to(target).as_posix()
                if any(k.casefold() == rel.casefold() and k != rel for k in payloads):raise RuntimeError("Case-colliding installed wheel payload")
                if rel in payloads and payloads[rel]!=expected:raise RuntimeError('Conflicting installed wheel payload')
                payloads[rel]=expected
    if not payloads:raise RuntimeError('Missing wheel population')
    for rel in ['env/Scripts/trapless-demo.exe','env/Scripts/python.exe','env/pyvenv.cfg']:
        payloads[rel]=digest(safe(target/rel))
    return payloads

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',type=Path,required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if os.name!='nt' or sys.version_info[:2]!=(3,12) or struct.calcsize('P')!=8:raise RuntimeError('Requires Windows x64 CPython 3.12')
    kit=safe(Path(__file__).parent);manifest=check_kit(kit);target=safe(a.target)
    if target==kit or target.is_relative_to(kit) or kit.is_relative_to(target):raise RuntimeError('Choose a dedicated installation outside the kit')
    binding={'kit_sha256':digest(kit/'KIT.json'),'target':str(target),'python':sys.version,'base_python':str(Path(sys.executable).resolve())}
    if target.exists() and not a.resume:raise RuntimeError('Target exists; explicitly resume its exact bound installation')
    if a.resume and not (target/'INSTALL_REQUEST.json').is_file():raise RuntimeError('No installation request to resume')
    target.mkdir(parents=True,exist_ok=True)
    with safe(target/'.install.lock').open('a+b') as lock:
        if os.fstat(lock.fileno()).st_size==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        request=target/'INSTALL_REQUEST.json'
        if request.exists():
            if read(request)!=binding:raise RuntimeError('Installation dependency changed; preserve it and choose a new target')
        else:
            if any(x.name!='.install.lock' for x in target.iterdir()):raise RuntimeError('Unbound nonempty installation target')
            save(request,binding)
        complete=target/'INSTALL_COMPLETE.json';launcher=target/'demo.ps1'
        launcher_bytes=("$ErrorActionPreference = 'Stop'\n& (Join-Path $PSScriptRoot 'env\\Scripts\\python.exe') -I -B -m traplesspke_demo @args\nexit $LASTEXITCODE\n").encode()
        if complete.exists():
            record=read(complete)
            if record.get('binding')!=binding or verify_install(kit,target,manifest)!=record.get('installed_payloads') or launcher.read_bytes()!=launcher_bytes:raise RuntimeError('Completed installation bytes changed')
            print('Verified retained completed installation:',target);return
        for marker in ['ENV_CREATED.json','PACKAGES_INSTALLED.json']:
            if (target/marker).exists() and read(target/marker).get('binding')!=binding:raise RuntimeError('Changed stage binding')
        interpreter=target/'env/Scripts/python.exe'
        if not (target/'ENV_CREATED.json').exists():
            if (target/'ENV_STARTED.json').exists():raise RuntimeError('Unacknowledged environment creation retained; select an explicit successor target')
            save(target/'ENV_STARTED.json',{'binding':binding,'producer_pid':os.getpid()})
            venv.EnvBuilder(with_pip=True,clear=False).create(target/'env')
            save(target/'ENV_CREATED.json',{'binding':binding,'producer_pid':os.getpid(),'interpreter_sha256':digest(interpreter)})
        if digest(safe(interpreter))!=read(target/'ENV_CREATED.json').get('interpreter_sha256'):raise RuntimeError('Bound interpreter changed')
        if not (target/'PACKAGES_INSTALLED.json').exists():
            if (target/'PACKAGES_STARTED.json').exists():raise RuntimeError('Unacknowledged or failed pip attempt retained; no blind relaunch')
            command=[str(interpreter),'-I','-B','-m','pip','--isolated','install','--no-cache-dir','--no-index','--find-links',str(kit/'wheels'),'--require-hashes','--only-binary=:all:','--no-compile','-r',str(kit/'install.lock')]
            save(target/'PACKAGES_STARTED.json',{'binding':binding,'command':command,'producer_pid':os.getpid()})
            with (target/'pip.log').open('x',encoding='utf-8') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
            save(target/'PACKAGES_EXIT.json',{'binding':binding,'actual_exit':result.returncode,'log_sha256':digest(target/'pip.log')})
            if result.returncode:raise RuntimeError('Offline pip failed; attempt retained')
            save(target/'PACKAGES_INSTALLED.json',{'binding':binding,'pip_exit':result.returncode})
        payloads=verify_install(kit,target,manifest);check_kit(kit)
        log_path=target/('runtime-check-'+uuid.uuid4().hex+'.log')
        with log_path.open('x',encoding='utf-8') as log:checked=subprocess.run([str(interpreter),'-I','-B','-m','traplesspke_demo','--version'],stdout=log,stderr=subprocess.STDOUT,timeout=60)
        if checked.returncode or log_path.read_text(encoding='utf-8').strip()!='0.1.4':raise RuntimeError('Installed entrypoint failed')
        launcher.write_bytes(launcher_bytes)
        save(complete,{'state':'INSTALLED_FROM_OFFLINE_KIT','binding':binding,'installed_payloads':payloads,'launcher_sha256':digest(launcher),'producer_pid':os.getpid(),'functional_replay':False,'security_acceptance':'NOT_ESTABLISHED'})
        print('Installed:',target/'env/Scripts/trapless-demo.exe')

if __name__=='__main__':main()
