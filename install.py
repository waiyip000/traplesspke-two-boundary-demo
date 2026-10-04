"""Compatibility entrypoint for the versioned offline installer."""
from pathlib import Path
import runpy
if __name__=="__main__":runpy.run_path(str(Path(__file__).with_name("install_r8.py")),run_name="__main__")
