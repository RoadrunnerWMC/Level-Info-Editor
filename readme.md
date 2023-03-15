# Level Info Editor 1.6

----------------------------------------------------------------

Level Info Editor is a program which can edit and save copies of LevelInfo.bin from Newer Super Mario Bros. Wii.

**Note:** World names as seen on the HUD and in the file select menu are not loaded from LevelInfo.bin. They are stored in the world map files themselves, and can be edited with Koopatlas. (The "Yoshi's Island" text displayed on a brand-new savefile slot is an exception; for technical reasons, this string is hardcoded.) To fully modify world names, you'll need to edit them in those places, too. [See this page for more details.](https://horizon.miraheze.org/wiki/Editing_World_Names)

----------------------------------------------------------------

### Getting Started

If you're using a source release:

- Python 3 (3.10 or newer recommended) — https://www.python.org
- PyQt 6.4 (or newer) (`pip install PyQt6`) **(RECOMMENDED)** or PyQt5 (`pip install PyQt5`)

If you have a prebuilt/frozen release (for Windows, macOS or Ubuntu),
you don't need to install anything — all the required libraries are included.


### macOS Troubleshooting

If you get the error "Level Info Editor is damaged and can't be opened.",
it's because the release builds are unsigned. To fix it, launch a Terminal
window and run

    sudo xattr -rd com.apple.quarantine "/path/to/Level Info Editor.app"

...with the example path above replaced with the actual path to the app. This
will override the application signature requirement, which should allow you to
launch the app.


### Level Info Editor Team

Developers:
 * RoadrunnerWMC - Developer


### Dependencies/Libraries/Resources

- Python 3 — The Python Software Foundation (https://www.python.org)
- Qt — The Qt Company (https://www.qt.io)
- PyQt — Riverbank Computing (https://riverbankcomputing.com/software/pyqt/intro)


### License

Level Info Editor is released under the GNU General Public License v3.
See the license file in the distribution for information.

----------------------------------------------------------------

## Changelog

Release 1.6 (March 15, 2023)
 * Added support for PyQt6. PyQt5 is also still supported.
 * The world list now shows world names in addition to world numbers
 * Broadly cleaned up the code (I'm much better at programming now, 10 years after I originally developed this)
   * The code for loading and saving files was almost completely rewritten. A few bugs were fixed during that process.

Release 1.5 (January 10, 2021)
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
