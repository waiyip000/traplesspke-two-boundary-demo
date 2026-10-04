"""Ordinary Windows routes; refuse aliases and redirected owned files."""
import os
from pathlib import Path
from .files_error import DemoError

def extended(value):
    text=str(Path(value).absolute())
    if text.startswith('\\\\?\\'):
        return Path(text)
    return Path('\\\\?\\UNC\\'+text[2:] if text.startswith('\\\\') else '\\\\?\\'+text)

def plain(value):
    text=os.fspath(value)
    if not isinstance(text,str) or not text or '\0' in text or text.startswith(('\\\\.\\','\\\\?\\')):
        raise DemoError('Invalid or device-namespace path')
    text=text.replace('/','\\')
    if text.startswith(('\\\\.\\','\\\\?\\')):
        raise DemoError('Device-namespace path')
    path=Path(text).absolute()
    reserved={'CON','PRN','AUX','NUL','CONIN$','CONOUT$',
              *(f'COM{i}' for i in '123456789\u00b9\u00b2\u00b3'),
              *(f'LPT{i}' for i in '123456789\u00b9\u00b2\u00b3')}
    for part in path.parts[1:]:
        if part in ('.','..'):continue
        if part.endswith((' ','.')) or part.split('.')[0].rstrip(' .').upper() in reserved or any(ord(c)<32 or c in ':<>"|?*' for c in part):
            raise DemoError('Invalid Windows path component')
    for item in (path,*path.parents):
        try:info=extended(item).lstat()
        except FileNotFoundError:continue
        if getattr(info,'st_file_attributes',0)&0x400:
            raise DemoError('Reparse route refused')
    return path.resolve()

def vacant(value):
    path=plain(value)
    try:extended(path).lstat()
    except FileNotFoundError:return path
    raise DemoError('Output already exists; choose a new path')

def members(folder):
    root=plain(folder)
    files={}
    base=extended(root)
    for item in base.rglob('*'):
        admitted=plain(root/item.relative_to(base))
        if extended(admitted).is_file():files[admitted.relative_to(root).as_posix()]=admitted
    return files
