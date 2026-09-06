# DSSATspatial initialization with dynamic environment patching

import os
import re
import shutil
import tempfile
import threading
import warnings
import inspect

# 1. Dynamic Environment Setup via Caller's Globals
# Peek into the notebook/script that is executing the import statement
_caller_globals = inspect.currentframe().f_back.f_globals

_dssat_version = _caller_globals.get('DSSAT_VERSION', '4.8.5')
_clean_version = _dssat_version.replace('.', '')

os.environ['DSSAT_EXE'] = f"dscsm0{_clean_version}.exe"
os.environ['DSSAT_DATA'] = f"Data_{_clean_version}"

# 2. Configure Temp Directory Dynamically
_system_temp = os.path.join(tempfile.gettempdir(), "DSSAT_Batch_Temp")
_custom_temp = _caller_globals.get('CUSTOM_TEMP', _system_temp)

if os.path.exists(_custom_temp):
    shutil.rmtree(_custom_temp, ignore_errors=True)
os.makedirs(_custom_temp, exist_ok=True)
os.environ['TMP'] = _custom_temp
os.environ['TEMP'] = _custom_temp
tempfile.tempdir = _custom_temp

# 3. Thread-Safe Symlink Patch to bypass Windows Administrator limits
_symlink_lock = threading.Lock()
_original_symlink = os.symlink

def _symlink_patch(src, dst, target_is_directory=False, *, dir_fd=None):
    with _symlink_lock:
        try:
            _original_symlink(src, dst, target_is_directory=target_is_directory, dir_fd=dir_fd)
        except OSError:
            if os.path.exists(dst):
                return
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
os.symlink = _symlink_patch
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Core Library Imports
VERSION = '048'

from . import crop
from .soil import SoilProfile, SoilLayer
from .weather import WeatherStation, WeatherRecord
from .run import DSSAT, BIN_PATH, STATIC_PATH
from . import filex
from .batch_processor import *