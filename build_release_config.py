import os.path

# Everything highly specific to Level Info Editor is in this section, to
# make it simpler to copypaste this script across all of the
# NSMBW-related projects that use the same technologies (Reggie, Puzzle,
# BRFNTify, etc)

PROJECT_NAME = 'Level Info Editor'
FULL_PROJECT_NAME = 'Level Info Editor'
PROJECT_VERSION = '1.0'

WIN_ICON = None
MAC_ICON = None
MAC_BUNDLE_IDENTIFIER = 'com.newerteam.lie'

SCRIPT_FILE = 'level_info_editor.py'
DATA_FOLDERS = []
DATA_FILES = ['charcodes.txt', 'license.txt', 'readme.md']
EXTRA_IMPORT_PATHS = []

USE_PYQT = True
USE_NSMBLIB = False

EXCLUDE_HASHLIB = True
EXCLUDE_INSPECT = False  # needed for dataclasses

# macOS only
AUTO_APP_BUNDLE_NAME = SCRIPT_FILE.split('.')[0] + '.app'
FINAL_APP_BUNDLE_NAME = FULL_PROJECT_NAME + '.app'
