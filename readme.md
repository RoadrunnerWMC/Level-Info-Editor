# Level Info Editor
(1.5)

----------------------------------------------------------------

Support:   http://rvlution.net/forums/  
On GitHub: https://github.com/RoadrunnerWMC/Level-Info-Editor  

----------------------------------------------------------------

Level Info Editor is a program which can edit and save copies of LevelInfo.bin from Newer Super Mario Bros. Wii.

**Note:** World names as seen on the HUD and in the file select menu are not loaded from LevelInfo.bin. They are stored in the world map files themselves, and can be edited with Koopatlas. (The "Yoshi's Island" text displayed on a brand-new savefile slot is an exception; for technical reasons, this string is hardcoded.) To fully modify world names, you'll need to edit them in those places, too. [See this page for more details.](https://horizon.miraheze.org/wiki/Editing_World_Names)

----------------------------------------------------------------

### Getting Started

If you're on Windows and don't care about having the bleeding-edge latest features, you can use the official Windows builds. This is by far the easiest setup method. Just download either a ZIP or 7Z file, unzip it and run the executable.

If you are not on Windows or you want the very latest features, you'll need to run Level Info Editor from source.


### How to Run Level Info Editor from Source

Download and install the following:
 * Python 3.4 (or newer) - http://www.python.org
 * PyQt 5.3 (or newer) - http://www.riverbankcomputing.co.uk/software/pyqt/intro
 * cx_Freeze 4.3 (or newer) (optional) - http://cx-freeze.sourceforge.net

Run the following in a command prompt:  
`python3 level_info_editor.py`  
You can replace `python3` with the path to python.exe (including "python.exe" at the end) and `level_info_editor.py` with the path to level_info_editor.py (including "level_info_editor.py" at the end)


### Level Info Editor Team

Developers:
 * RoadrunnerWMC - Developer

### Dependencies/Libraries/Resources

Python 3 - Python Software Foundation (https://www.python.org)  
Qt 5 - Nokia (http://qt.nokia.com)  
PyQt5 - Riverbank Computing (http://www.riverbankcomputing.co.uk/software/pyqt/intro)  
cx_Freeze - Anthony Tuininga (http://cx-freeze.sourceforge.net)


### License

Level Info Editor is released under the GNU General Public License v3.
See the license file in the distribution for information.

----------------------------------------------------------------

## Changelog

Release 1.5: (January 10, 2021)
 * Fixed issues with modern PyQt versions
 * Started providing builds for 64-bit Windows, Linux, and macOS

*Note: there was no official release 1.4. The repository code was marked as "1.4" for many years, so I skipped ahead to 1.5 in order to distinguish that release from that.*

Release 1.3 (August 2, 2014)
 * Added license.txt and license headers to the source files
 * New readme
 * Dropped Python 2 support
 * Added PyQt5 support
 * Switched from py2exe to cx_Freeze

Release 1.2.1 (August 9, 2013)
 * Fixed a small bug

Release 1.2 (August 8, 2013)
 * Keyboard shortcuts added
 * Drag-and-drop support added

Release 1.1 (July 22, 2013)
 * "World Sections" tab has been replaced with the
   new user-friendly "World Options" tab.
 * Some level settings have been changed/updated.
 * New tooltips have been added to most window items.
   If you don't understand something, hover over it!
 * Fixed a bug in which Windows EXEs don't close when
   File->Exit is clicked.

Release 1.0 (July 19, 2013)
 * Initial release!
