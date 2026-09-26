#!/Users/dionlava/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"""Batch front end to KiCad's bundled ngspice shared library; no installation."""
import ctypes as c,sys
from pathlib import Path
lib=c.CDLL('/Applications/KiCad/KiCad.app/Contents/Frameworks/libngspice.0.dylib')
C=c.CFUNCTYPE(c.c_int,c.c_char_p,c.c_int,c.c_void_p)
X=c.CFUNCTYPE(c.c_int,c.c_int,c.c_bool,c.c_bool,c.c_int,c.c_void_p)
@C
def output(text,ident,data):
 print(text.decode(errors='replace'),flush=True);return 0
@C
def status(text,ident,data):return 0
@X
def close(code,immediate,quit_,ident,data):return 0
lib.ngSpice_Init.argtypes=[C,C,X,c.c_void_p,c.c_void_p,c.c_void_p,c.c_void_p]
lib.ngSpice_Init(output,status,close,None,None,None,None)
lib.ngSpice_Command.argtypes=[c.c_char_p]
files=[a for a in sys.argv[1:] if not a.startswith('-')]
if not files:raise SystemExit('Pass a circuit file')
path=Path(files[-1]).resolve()
result=lib.ngSpice_Command(('source '+str(path)).encode())
raise SystemExit(0)
