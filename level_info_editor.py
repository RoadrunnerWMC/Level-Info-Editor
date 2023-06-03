#!/usr/bin/python
# -*- coding: latin-1 -*-

# Level Info Editor - Edits NewerSMBW's LevelInfo.bin
# Version 1.6
# Copyright (C) 2013-2023 RoadrunnerWMC

# This file is part of Level Info Editor.

# Level Info Editor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Level Info Editor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Level Info Editor.  If not, see <http://www.gnu.org/licenses/>.



# level_info_editor.py
# This is the main executable for Level Info Editor


################################################################
################################################################


VERSION = '1.6'

import dataclasses
import struct
import sys
from typing import List, Optional

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
except ImportError:
    from PyQt5 import QtCore, QtGui, QtWidgets


@dataclasses.dataclass
class LevelInfo():
    """Represents a level"""
    name: str = ''
    file_world: int = 0
    file_level: int = 0
    display_world: int = 0
    display_level: int = 0
    in_star_coins_menu: bool = True
    has_normal_exit: bool = False
    has_secret_exit: bool = False
    is_right_side: bool = False

    @property
    def flags(self) -> int:
        flags = 0
        if self.in_star_coins_menu: flags |= 0x0002
        if self.has_normal_exit:    flags |= 0x0010
        if self.has_secret_exit:    flags |= 0x0020
        if self.is_right_side:      flags |= 0x0400
        return flags
    @flags.setter
    def flags(self, value: int) -> None:
        self.in_star_coins_menu = bool(value & 0x0002)
        self.has_normal_exit    = bool(value & 0x0010)
        self.has_secret_exit    = bool(value & 0x0020)
        self.is_right_side      = bool(value & 0x0400)


@dataclasses.dataclass
class WorldInfo():
    """Represents a world"""
    world_number: Optional[int] = None
    has_left: bool = False
    has_right: bool = False
    name_left: str = ''
    name_right: str = ''
    levels: List[LevelInfo] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class LevelInfoFile():
    """Represents LevelInfo.bin"""
    worlds: List[WorldInfo] = dataclasses.field(default_factory=list)
    comments: str = ''

    @classmethod
    def from_data(cls, data: bytes) -> 'LevelInfoFile':
        """Create a LevelInfoFile from file data"""

        # Check for the file header
        if not data.startswith(b'NWRp'):
            return

        magic, num_worlds = struct.unpack_from('>4sI', data, 0)
        world_offsets = struct.unpack_from(f'>{num_worlds}I', data, 0x08)

        # Load the worlds
        min_text_offs = 0xFFFFFFFF
        worlds = []
        LEVEL_ENTRY_STRUCT = struct.Struct('>5BxHI')
        for world_i, world_offset in enumerate(world_offsets):
            num_levels, = struct.unpack_from(f'>I', data, world_offset)

            # Make a world and add levels/headers to it
            world = WorldInfo()

            for level_offs in range(world_offset + 4, world_offset + 4 + num_levels * 12, 12):
                (
                    file_name_w, file_name_l,
                    display_name_w, display_name_l,
                    text_len, flags, text_offs,
                ) = LEVEL_ENTRY_STRUCT.unpack_from(data, level_offs)

                min_text_offs = min(min_text_offs, text_offs)
                text_enc = data[text_offs : text_offs + text_len]
                text = bytes((c + 0x30) & 0xff for c in text_enc).decode('ascii')

                # Add header info or levels
                if display_name_l >= 100:
                    # It's a world header
                    world.world_number = display_name_w
                    if display_name_l == 100:
                        world.has_left = True
                        world.name_left = text
                    else:
                        world.has_right = True
                        world.name_right = text
                else:
                    # It's a real level
                    world.levels.append(LevelInfo(
                        name=text,
                        file_world=(file_name_w + 1),
                        file_level=(file_name_l + 1),
                        display_world=display_name_w,
                        display_level=display_name_l))
                    world.levels[-1].flags = flags

            # Add it to worlds
            worlds.append(world)

        # Create instance
        self = cls(worlds)

        # Get the comments
        self.comments = data[self.get_comments_offset() : min_text_offs - 1].decode('ascii')

        return self

    def get_comments_offset(self) -> int:
        """Calculate the offset of the comments data"""
        # I'm trying to make this as easy-to-read as possible.
        offset = 0

        offset += 4  # "NWRp" text
        offset += 4  # Number-of-worlds bytes
        for world in self.worlds:
            offset += 4  # Offset to the world data in the file header
            offset += 4  # Number-of-levels bytes

            if world.has_left: offset += 12  # Data for that takes 12 bytes
            if world.has_right: offset += 12  # Same as above
            for level in world.levels:
                offset += 12  # Each level is 12 bytes

        return offset

    def save(self) -> bytes:
        """Return LevelInfo.bin file data"""
        result = bytearray()
        text_start = self.get_comments_offset() + len(self.comments) + 1

        # First things first - add "NWRp"
        result.extend(b'NWRp')

        # Add the number-of-worlds value (we'll only worry about the last 2 bytes)
        result.extend(struct.pack('>I', len(self.worlds)))

        # Add blank spaces for each world value
        result.extend(b'\0\0\0\0' * len(self.worlds))

        # Add worlds and world-offsets at the same time
        current_offs = len(result)
        current_text_offs = text_start
        text = bytearray()
        LEVEL_ENTRY_STRUCT = struct.Struct('>5BxHI')
        for i, world in enumerate(self.worlds):
            # Set the world-offset start value to current_offs
            struct.pack_into('>I', result, 8 + i * 4, current_offs)

            # Create a place to store some world info
            world_data = bytearray()

            # Add the number-of-levels value
            num = len(world.levels)
            if world.has_left: num += 1
            if world.has_right: num += 1
            world_data.extend(struct.pack('>I', num))

            # Add data to world_data for each world half
            for exists, name in zip((world.has_left, world.has_right), ('left', 'right')):
                if not exists: continue
                w_name = getattr(world, f'name_{name}')
                world_data.extend(LEVEL_ENTRY_STRUCT.pack(
                    98, 98,  # filename: 98-98
                    world.world_number, (101 if name == 'right' else 100),  # display name: WN-100
                    len(w_name),
                    (0x400 if name == 'right' else 0),
                    current_text_offs))

                current_text_offs += len(w_name) + 1
                text.extend(w_name.encode('ascii') + b'\0')

            # Add data to world_data for each level
            for level in world.levels:
                world_data.extend(LEVEL_ENTRY_STRUCT.pack(
                    (level.file_world - 1) & 0xff, (level.file_level - 1) & 0xff,
                    level.display_world, level.display_level,
                    len(level.name),
                    level.flags,
                    current_text_offs))

                current_text_offs += len(level.name) + 1
                text.extend(level.name.encode('ascii') + b'\0')

            # Add world_data to result
            result.extend(world_data)
            current_offs += len(world_data)

        # Add the comments
        result.extend(self.comments.encode('ascii') + b'\0')

        # Add text
        result.extend([(c - 0x30) & 0xff for c in text])

        return bytes(result)


########################################################################
########################################################################
########################################################################
########################################################################


# Drag-and-Drop Picker
class DNDPicker(QtWidgets.QListWidget):
    """A list widget which calls a function when an item's been moved"""
    def __init__(self, handler):
        super().__init__()
        self.handler = handler
        self.setDragDropMode(QtWidgets.QListWidget.DragDropMode.InternalMove)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        QtWidgets.QListWidget.dropEvent(self, event)
        self.handler()


class LevelInfoViewer(QtWidgets.QWidget):
    """Widget that views level info"""
    def __init__(self):
        super().__init__()
        self.file = LevelInfoFile()

        # Create the Worlds widgets
        worlds_box = QtWidgets.QGroupBox('Worlds')
        self.world_picker = DNDPicker(self.handle_world_drag_drop)
        self.add_world_button = QtWidgets.QPushButton('Add')
        self.remove_world_button = QtWidgets.QPushButton('Remove')

        # Add some tooltips
        self.add_world_button.setToolTip('<b>Add:</b><br>Adds a world to the file.')
        self.remove_world_button.setToolTip('<b>Remove:</b><br>Removes the currently selected world from the file.')

        # Disable some
        self.remove_world_button.setEnabled(False)

        # Connect them to handlers
        self.world_picker.currentItemChanged.connect(self.handle_world_select)
        self.add_world_button.clicked.connect(self.handle_add_world)
        self.remove_world_button.clicked.connect(self.handle_remove_world)

        # Make a layout
        L = QtWidgets.QGridLayout(worlds_box)
        L.addWidget(self.world_picker, 0, 0, 1, 2)
        L.addWidget(self.add_world_button, 1, 0)
        L.addWidget(self.remove_world_button, 1, 1)


        # Create the World Options widget
        self.world_editor = WorldOptionsEditor()
        self.world_editor.data_changed.connect(self.handle_world_data_change)


        # Create the Levels widgets
        levels_box = QtWidgets.QWidget()
        self.level_picker = DNDPicker(self.handle_level_drag_drop)
        self.level_editor = LevelEditor()
        self.add_level_button = QtWidgets.QPushButton('Add')
        self.remove_level_button = QtWidgets.QPushButton('Remove')

        # Add some tooltips
        self.add_level_button.setToolTip('<b>Add:</b><br>Adds a level to the currently selected world.')
        self.remove_level_button.setToolTip('<b>Remove:</b><br>Removes the currently selected level from the world.')

        # Disable some
        self.add_level_button.setEnabled(False)
        self.remove_level_button.setEnabled(False)

        # Connect them to handlers
        self.level_picker.currentItemChanged.connect(self.handle_level_select)
        self.level_editor.data_changed.connect(self.handle_level_data_change)
        self.level_editor.nav_request.connect(self.handle_level_nav_request)
        self.add_level_button.clicked.connect(self.handle_add_level)
        self.remove_level_button.clicked.connect(self.handle_remove_level)

        # Make a layout
        L = QtWidgets.QGridLayout(levels_box)
        L.addWidget(self.level_picker, 0, 0, 1, 2)
        L.addWidget(self.add_level_button, 1, 0)
        L.addWidget(self.remove_level_button, 1, 1)
        L.addWidget(self.level_editor, 2, 0, 1, 2)


        # Create the Comments editor and layout
        comments_box = QtWidgets.QWidget()
        label = QtWidgets.QLabel('You can add comments to the file here:')
        self.comments_editor = QtWidgets.QPlainTextEdit()

        self.comments_editor.textChanged.connect(self.handle_comments_changed)

        L = QtWidgets.QVBoxLayout(comments_box)
        L.addWidget(label)
        L.addWidget(self.comments_editor)


        # Create the tab widget
        tab = QtWidgets.QTabWidget()
        tab.addTab(self.world_editor, 'World Options')
        tab.addTab(levels_box, 'Levels')
        tab.addTab(comments_box, 'Comments')

        # Make a main layout
        L = QtWidgets.QHBoxLayout(self)
        L.addWidget(worlds_box)
        L.addWidget(tab)

    def set_file(self, file: LevelInfoFile) -> None:
        """Change the file to view"""
        self.file = file

        self.world_picker.clear()
        self.level_picker.clear()

        # Add worlds
        for world in self.file.worlds:
            item = QtWidgets.QListWidgetItem()  # self.update_names() will add the name
            item.setData(QtCore.Qt.ItemDataRole.UserRole, world)
            self.world_picker.addItem(item)

        # Add comments
        self.comments_editor.setPlainText(self.file.comments)

        # Update world names
        self.update_names()

    def update_names(self) -> None:
        """Update item names in all three item-picker widgets"""
        for item in self.world_picker.findItems('', QtCore.Qt.MatchFlag.MatchContains):
            world = item.data(QtCore.Qt.ItemDataRole.UserRole)

            text = 'World '
            if world.world_number is None:
                text += '?'
            else:
                text += str(world.world_number)

                half_names = []
                if world.has_left: half_names.append(world.name_left.strip())
                if world.has_right: half_names.append(world.name_right.strip())
                while '' in half_names:
                    half_names.remove('')

                if half_names:
                    text += f' ({", ".join(half_names)})'

            item.setText(text)

        for item in self.level_picker.findItems('', QtCore.Qt.MatchFlag.MatchContains):
            level = item.data(QtCore.Qt.ItemDataRole.UserRole)
            item.setText(level.name)

    def save_file(self) -> bytes:
        """Return the file in saved form"""
        return self.file.save()  # self.file does this for us


    # World functions

    def handle_world_select(self) -> None:
        """Handle the user picking a world"""
        self.world_editor.clear()
        self.level_picker.clear()
        self.level_editor.clear()

        # Get the current item (it's None if nothing's selected)
        current_item = self.world_picker.currentItem()

        # Enable/disable buttons
        if current_item is None:
            self.remove_world_button.setEnabled(False)
            self.add_level_button.setEnabled(False)
            self.remove_level_button.setEnabled(False)
        else:
            index = self.world_picker.indexFromItem(current_item).row()
            num_items = self.world_picker.count()

            self.remove_world_button.setEnabled(True)
            self.add_level_button.setEnabled(True)

        # Get the world
        if current_item is None: return
        world = current_item.data(QtCore.Qt.ItemDataRole.UserRole)

        # Set up the World Options Editor
        self.world_editor.set_world(world)

        # Add levels to self.level_picker
        for level in world.levels:
            item = QtWidgets.QListWidgetItem(level.name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, level)
            self.level_picker.addItem(item)
        self.level_picker.setCurrentRow(0)


    def handle_add_world(self) -> None:
        """Handle "Add World" button clicks"""
        world = WorldInfo()
        text = 'World (unknown)'

        # Add it to self.file and self.world_picker
        self.file.worlds.append(world)
        item = QtWidgets.QListWidgetItem(text)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, world)
        self.world_picker.addItem(item)
        self.world_picker.scrollToItem(item)
        item.setSelected(True)

        self.update_names()

    def handle_remove_world(self) -> None:
        """Handle "Remove World" button clicks"""
        item = self.world_picker.currentItem()
        world = item.data(QtCore.Qt.ItemDataRole.UserRole)

        # Remove it from file and the picker
        self.file.worlds.remove(world)
        self.world_picker.takeItem(self.world_picker.row(item))

        self.update_names()

    def handle_world_drag_drop(self) -> None:
        """Handle dragging-and-dropping in the world picker"""
        new_worlds = []
        for item in self.world_picker.findItems('', QtCore.Qt.MatchFlag.MatchContains):
            new_worlds.append(item.data(QtCore.Qt.ItemDataRole.UserRole))
        self.file.worlds = new_worlds

        self.update_names()

    def handle_world_data_change(self) -> None:
        """Handle the user changing world data"""
        self.update_names()


    # Level functions

    def handle_level_select(self) -> None:
        """Handle the user picking a level"""
        self.level_editor.clear()

        # Get the current item (it's None if nothing's selected)
        current_item = self.level_picker.currentItem()

        # Enable/disable buttons
        if current_item is None:
            self.remove_level_button.setEnabled(False)
        else:
            index = self.level_picker.indexFromItem(current_item).row()
            num_items = self.level_picker.count()

            self.remove_level_button.setEnabled(True)

        # Get the level
        if current_item is None: return
        level = current_item.data(QtCore.Qt.ItemDataRole.UserRole)

        # Set LevelEdit to edit it
        self.level_editor.setLevel(level)

    def handle_level_data_change(self) -> None:
        """Handle the user changing level data"""
        self.update_names()

    def handle_level_nav_request(self, is_up: bool, refocus_widget: QtWidgets.QWidget) -> None:
        """Handle the user pressing PgUp or PgDn to switch between levels"""
        current_row = self.level_picker.currentRow()

        new_row = current_row + (-1 if is_up else 1)
        new_row = max(0, new_row)
        new_row = min(new_row, self.level_picker.count() - 1)

        if new_row != current_row:
            self.level_picker.setCurrentRow(new_row)
            refocus_widget.setFocus(True)

    def handle_add_level(self) -> None:
        """Handle "Add Level" button clicks"""
        level = LevelInfo(name='New Level')
        item = QtWidgets.QListWidgetItem(level.name)
        item.setData(QtCore.Qt.ItemDataRole.UserRole, level)

        # Add it to the current world and self.level_picker
        world = self.world_picker.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)
        world.levels.append(level)
        self.level_picker.addItem(item)
        self.level_picker.scrollToItem(item)
        item.setSelected(True)

        self.update_names()

    def handle_remove_level(self) -> None:
        """Handle "Remove Level" button clicks"""
        item = self.level_picker.currentItem()
        level = item.data(QtCore.Qt.ItemDataRole.UserRole)

        # Remove it from file and the picker
        world = self.world_picker.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)
        world.levels.remove(level)
        self.level_picker.takeItem(self.level_picker.row(item))

        self.update_names()

    def handle_level_drag_drop(self) -> None:
        """Handle dragging-and-dropping in the level picker"""
        world = self.world_picker.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)

        new_levels = []
        for item in self.level_picker.findItems('', QtCore.Qt.MatchFlag.MatchContains):
            new_levels.append(item.data(QtCore.Qt.ItemDataRole.UserRole))

        world = self.world_picker.currentItem().data(QtCore.Qt.ItemDataRole.UserRole)
        world.levels = new_levels

        self.update_names()


    # Comments functions

    def handle_comments_changed(self) -> None:
        """Handle comments changes"""
        self.file.comments = str(self.comments_editor.toPlainText())





########################################################################
########################################################################
########################################################################
########################################################################


class WorldOptionsEditor(QtWidgets.QWidget):
    """Widget that allows the user to change world settings"""
    data_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.world = None

        # Create the data-editing widgets
        self.number_edit = QtWidgets.QSpinBox()
        self.number_edit.setMaximum(255)
        self.left_exists_edit = QtWidgets.QCheckBox()
        self.left_name_edit = QtWidgets.QLineEdit()
        self.left_name_edit.setMaxLength(255)
        self.right_exists_edit = QtWidgets.QCheckBox()
        self.right_name_edit = QtWidgets.QLineEdit()
        self.right_name_edit.setMaxLength(255)

        # Add some tooltips
        number_warning = "<br><br><b>Note:</b><br>You can only set the world's World Number if you have at least one world half turned on!"
        self.number_edit.setToolTip("<b>World Number:</b><br>Changes the currently selected world's World Number." + number_warning)
        self.left_exists_edit.setToolTip('<b>Has a 1st Half:</b><br>If this is checked, the currently selected world will have a first half.' + number_warning)
        self.left_name_edit.setToolTip('<b>1st Half Name:</b><br>Changes the name for the first half of the world.')
        self.right_exists_edit.setToolTip('<b>Has a 2nd Half:</b><br>If this is checked, the currently selected world will have a second half.' + number_warning)
        self.right_name_edit.setToolTip('<b>2nd Half Name:</b><br>Changes the name for the second half of the world.')

        # Disable them all
        self.number_edit.setEnabled(False)
        self.left_exists_edit.setEnabled(False)
        self.left_name_edit.setEnabled(False)
        self.right_exists_edit.setEnabled(False)
        self.right_name_edit.setEnabled(False)

        # Connect them to handlers
        self.number_edit.valueChanged.connect(self.handle_number_change)
        self.left_exists_edit.stateChanged.connect(self.handle_left_exists_change)
        self.left_name_edit.textEdited.connect(self.handle_left_name_change)
        self.right_exists_edit.stateChanged.connect(self.handle_right_exists_change)
        self.right_name_edit.textEdited.connect(self.handle_right_name_change)

        # Create a layout
        L = QtWidgets.QFormLayout(self)
        L.addRow('World Number:', self.number_edit)
        L.addRow('Has a 1st Half:', self.left_exists_edit)
        L.addRow('1st Half Name:', self.left_name_edit)
        L.addRow('Has a 2nd Half:', self.right_exists_edit)
        L.addRow('2nd Half Name:', self.right_name_edit)


    def clear(self) -> None:
        """Clear all data from the WorldOptionsEditor"""
        self.world = None

        # Disable the boxes
        self.number_edit.setEnabled(False)
        self.left_exists_edit.setEnabled(False)
        self.left_name_edit.setEnabled(False)
        self.right_exists_edit.setEnabled(False)
        self.right_name_edit.setEnabled(False)

        # Set them all to defaults
        self.number_edit.setValue(0)
        self.left_exists_edit.setChecked(False)
        self.left_name_edit.setText('')
        self.right_exists_edit.setChecked(False)
        self.right_name_edit.setText('')

    def set_world(self, world: WorldInfo) -> None:
        """Set the world to be edited"""
        self.world = world

        # Enable the first box, and potentially others
        if world.has_left or world.has_right:
            self.number_edit.setEnabled(True)
        self.left_exists_edit.setEnabled(True)
        self.left_name_edit.setEnabled(world.has_left)
        self.right_exists_edit.setEnabled(True)
        self.right_name_edit.setEnabled(world.has_right)

        # Set them to the correct values
        if world.has_left or world.has_right:
            self.number_edit.setValue(world.world_number)
        self.left_exists_edit.setChecked(world.has_left)
        if world.has_left:
            self.left_name_edit.setText(world.name_left)
        self.right_exists_edit.setChecked(world.has_right)
        if world.has_right:
            self.right_name_edit.setText(world.name_right)

    def handle_number_change(self) -> None:
        """Handle self.number_edit changes"""
        if self.world is None: return
        self.world.world_number = self.number_edit.value()
        self.data_changed.emit()

    def handle_left_exists_change(self) -> None:
        """Handle self.left_exists_edit changes"""
        if self.world is None: return
        self.world.has_left = self.left_exists_edit.isChecked()
        self.left_name_edit.setEnabled(self.world.has_left)
        if not self.world.has_left:
            self.left_name_edit.setText('')
        self.number_edit.setEnabled(self.world.has_left or self.world.has_right)
        if (not self.world.has_left) and (not self.world.has_right):
            self.world.world_number = None
            self.number_edit.setValue(0)
        elif self.world.world_number is None:
            self.world.world_number = 0
            self.number_edit.setValue(0)
        self.data_changed.emit()

    def handle_left_name_change(self) -> None:
        """Handle self.left_name_edit changes"""
        if self.world is None: return
        self.world.name_left = str(self.left_name_edit.text())
        self.data_changed.emit()

    def handle_right_exists_change(self) -> None:
        """Handle self.right_exists_edit changes"""
        if self.world is None: return
        self.world.has_right = self.right_exists_edit.isChecked()
        self.right_name_edit.setEnabled(self.world.has_right)
        if not self.world.has_right: self.right_name_edit.setText('')
        self.number_edit.setEnabled(self.world.has_left or self.world.has_right)
        if (not self.world.has_left) and (not self.world.has_right):
            self.world.world_number = None
            self.number_edit.setValue(0)
        elif self.world.world_number is None:
            self.world.world_number = 0
            self.number_edit.setValue(0)
        self.data_changed.emit()

    def handle_right_name_change(self) -> None:
        """Handle self.right_name_edit changes"""
        if self.world is None: return
        self.world.name_right = str(self.right_name_edit.text())
        self.data_changed.emit()





class LevelEditor(QtWidgets.QGroupBox):
    """Widget that allows the user to change level settings"""
    data_changed = QtCore.pyqtSignal()
    nav_request = QtCore.pyqtSignal(bool, QtWidgets.QWidget)

    def __init__(self):
        super().__init__()
        self.setTitle('Level')
        self.level = None

        # Create the data-editing widgets
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setMaxLength(255)
        self.file_edit = LevelNameEdit()
        self.file_edit.set_minimums(1, 1)
        self.display_edit = LevelNameEdit()
        self.in_star_coins_menu_edit = QtWidgets.QCheckBox()
        self.has_normal_exit_edit = QtWidgets.QCheckBox()
        self.has_secret_exit_edit = QtWidgets.QCheckBox()
        self.world_half_edit = QtWidgets.QComboBox()
        self.world_half_edit.addItems(['1st Half', '2nd Half'])

        # Add some tooltips
        self.name_edit.setToolTip("<b>Name:</b><br>Changes the level's name.")
        self.file_edit.setToolTip('<b>Filename:</b><br>Changes the name of the file the level will load from (.arc is automatically added).')
        self.display_edit.setToolTip("<b>Display Name:</b><br>Changes the on-screen name of this level.<br><br><b>Note:</b><br>Special characters are often used here - symbols such as Castle, Tower, Boo House and Toad House. Each can be used by picking a specific number. Look at Newer SMBW's original LevelInfo.bin to find some!")
        self.in_star_coins_menu_edit.setToolTip('<b>Star Coins Menu:</b><br>If this is checked, the level will appear in the Star Coins Menu.')
        self.has_normal_exit_edit.setToolTip('<b>Normal Exit:</b><br>If this is checked, the level will have a normal exit.')
        self.has_secret_exit_edit.setToolTip('<b>Secret Exit:</b><br>If this is checked, the level will have a secret exit.')
        self.world_half_edit.setToolTip('<b>World Half:</b><br>This changes which side of the Star Coins menu the level appears on.')

        # Disable them
        self.name_edit.setEnabled(False)
        self.file_edit.setEnabled(False)
        self.display_edit.setEnabled(False)
        self.in_star_coins_menu_edit.setEnabled(False)
        self.has_normal_exit_edit.setEnabled(False)
        self.has_secret_exit_edit.setEnabled(False)
        self.world_half_edit.setEnabled(False)

        # Connect them to handlers
        self.name_edit.textEdited.connect(self.handle_name_change)
        self.file_edit.data_changed.connect(self.handle_file_change)
        self.display_edit.data_changed.connect(self.handle_display_change)
        self.in_star_coins_menu_edit.stateChanged.connect(self.handle_star_coins_menu_change)
        self.has_normal_exit_edit.stateChanged.connect(self.handle_has_normal_exit_change)
        self.has_secret_exit_edit.stateChanged.connect(self.handle_has_secret_exit_change)
        self.world_half_edit.currentIndexChanged.connect(self.handle_world_half_change)

        # Create a layout
        L = QtWidgets.QFormLayout(self)
        L.addRow('Name:', self.name_edit)
        L.addRow('Filename:', self.file_edit)
        L.addRow('Display Name:', self.display_edit)
        L.addRow('Normal Exit:', self.has_normal_exit_edit)
        L.addRow('Secret Exit:', self.has_secret_exit_edit)
        L.addRow('Star Coins Menu:', self.in_star_coins_menu_edit)
        L.addRow('World Half:', self.world_half_edit)

        # Watch for PageUp/PageDown
        for leaf_widget in [self.name_edit,
                            self.file_edit.world_num_edit,
                            self.file_edit.level_num_edit,
                            self.display_edit.world_num_edit,
                            self.display_edit.level_num_edit,
                            self.has_normal_exit_edit,
                            self.has_secret_exit_edit,
                            self.in_star_coins_menu_edit,
                            self.world_half_edit]:
            leaf_widget.installEventFilter(self)


    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Filter events for leaf widgets, looking for PageUp/PageDown"""
        # Changing the selected level causes the field edit widget to
        # lose focus, so we pass it in the signal and ask that the
        # handler function please refocus it after switching levels.
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_PageUp:
                self.nav_request.emit(True, obj)
                return True
            elif event.key() == QtCore.Qt.Key.Key_PageDown:
                self.nav_request.emit(False, obj)
                return True

        return super().eventFilter(obj, event)

    def clear(self) -> None:
        """Clear all data from the LevelEditor"""
        self.level = None
        self.setTitle('Level')

        # Disable all of the data-editing widgets
        self.name_edit.setEnabled(False)
        self.file_edit.setEnabled(False)
        self.display_edit.setEnabled(False)
        self.in_star_coins_menu_edit.setEnabled(False)
        self.has_normal_exit_edit.setEnabled(False)
        self.has_secret_exit_edit.setEnabled(False)
        self.world_half_edit.setEnabled(False)

        # Set them all to '', 0, and False
        self.name_edit.setText('')
        self.file_edit.reset()
        self.display_edit.reset()
        self.in_star_coins_menu_edit.setChecked(False)
        self.has_normal_exit_edit.setChecked(False)
        self.has_secret_exit_edit.setChecked(False)
        self.world_half_edit.setCurrentIndex(0)

    def setLevel(self, level: LevelInfo) -> None:
        """Set the level to be edited"""
        self.level = level
        self.setTitle(self.level.name)

        # Enable all of the data-editing widgets
        self.name_edit.setEnabled(True)
        self.file_edit.setEnabled(True)
        self.display_edit.setEnabled(True)
        self.in_star_coins_menu_edit.setEnabled(True)
        self.has_normal_exit_edit.setEnabled(True)
        self.has_secret_exit_edit.setEnabled(True)
        self.world_half_edit.setEnabled(True)

        # Set them to the correct values
        self.name_edit.setText(level.name)
        self.file_edit.set_data(level.file_world, level.file_level)
        self.display_edit.set_data(level.display_world, level.display_level)
        self.in_star_coins_menu_edit.setChecked(level.in_star_coins_menu)
        self.has_normal_exit_edit.setChecked(level.has_normal_exit)
        self.has_secret_exit_edit.setChecked(level.has_secret_exit)
        self.world_half_edit.setCurrentIndex(1 if level.is_right_side else 0)

    def handle_name_change(self) -> None:
        """Handle self.name_edit changes"""
        if self.level is None: return
        self.level.name = str(self.name_edit.text())
        self.data_changed.emit()
        self.setTitle('Level - ' + self.level.name)

    def handle_file_change(self) -> None:
        """Handle self.file_edit changes"""
        if self.level is None: return
        self.level.file_world = self.file_edit.get_world()
        self.level.file_level = self.file_edit.get_level()
        self.data_changed.emit()

    def handle_display_change(self) -> None:
        """Handle self.display_edit changes"""
        if self.level is None: return
        self.level.display_world = self.display_edit.get_world()
        self.level.display_level = self.display_edit.get_level()
        self.data_changed.emit()

    def handle_star_coins_menu_change(self) -> None:
        """Handle self.in_star_coins_menu_edit changes"""
        if self.level is None: return
        self.level.in_star_coins_menu = self.in_star_coins_menu_edit.isChecked()
        self.data_changed.emit()

    def handle_has_normal_exit_change(self) -> None:
        """Handle self.has_normal_exit_edit changes"""
        if self.level is None: return
        self.level.has_normal_exit = self.has_normal_exit_edit.isChecked()
        self.data_changed.emit()

    def handle_has_secret_exit_change(self) -> None:
        """Handle self.has_secret_exit_edit changes"""
        if self.level is None: return
        self.level.has_secret_exit = self.has_secret_exit_edit.isChecked()
        self.data_changed.emit()

    def handle_world_half_change(self) -> None:
        """Handle self.world_half_edit changes"""
        if self.level is None: return
        self.level.is_right_side = (self.world_half_edit.currentIndex() == 1)
        self.data_changed.emit()



class LevelNameEdit(QtWidgets.QWidget):
    """Widget that allows a level name to be edited"""
    data_changed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.world_num_edit = QtWidgets.QSpinBox()
        self.world_num_edit.setMaximum(255)
        dash_label = QtWidgets.QLabel('-')
        dash_label.setMaximumWidth(dash_label.minimumSizeHint().width())
        self.level_num_edit = QtWidgets.QSpinBox()
        self.level_num_edit.setMaximum(255)

        self.world_num_edit.valueChanged.connect(self.emit_data_change)
        self.level_num_edit.valueChanged.connect(self.emit_data_change)

        L = QtWidgets.QHBoxLayout(self)
        L.setContentsMargins(0, 0, 0, 0)
        L.addWidget(self.world_num_edit)
        L.addWidget(dash_label)
        L.addWidget(self.level_num_edit)

    def set_data(self, world_num: int, level_num: int) -> None:
        """Set the world and level values"""
        self.world_num_edit.setValue(world_num)
        self.level_num_edit.setValue(level_num)

    def get_world(self) -> int:
        """Return the world value"""
        return self.world_num_edit.value()

    def get_level(self) -> int:
        """Return the level value"""
        return self.level_num_edit.value()

    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the widget"""
        self.world_num_edit.setEnabled(enabled)
        self.level_num_edit.setEnabled(enabled)

    def reset(self) -> None:
        """Reset the widget"""
        self.world_num_edit.setValue(0)
        self.level_num_edit.setValue(0)

    def emit_data_change(self) -> None:
        """Emit the data_changed signal"""
        self.data_changed.emit()

    def set_minimums(self, world_minimum: int, level_minimum: int) -> None:
        """Set the minimum for each spinbox"""
        self.world_num_edit.setMinimum(world_minimum)
        self.level_num_edit.setMinimum(level_minimum)



########################################################################
########################################################################
########################################################################
########################################################################



class MainWindow(QtWidgets.QMainWindow):
    """Main window"""
    def __init__(self):
        super().__init__()
        self.file_path = None

        self.view = LevelInfoViewer()
        self.setCentralWidget(self.view)

        self.create_menu_bar()

        self.setWindowTitle('Level Info Editor')
        self.show()

    def create_menu_bar(self) -> None:
        """Set up the menu bar"""
        m = self.menuBar()

        # File menu
        f = m.addMenu('&File')

        open_action = f.addAction('Open File...')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.handle_open)

        self.save_action = f.addAction('Save File')
        self.save_action.setShortcut('Ctrl+S')
        self.save_action.triggered.connect(self.handle_save)
        self.save_action.setEnabled(False)

        save_as_action = f.addAction('Save File As...')
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.handle_save_as)

        f.addSeparator()

        exit_action = f.addAction('Exit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.handle_exit)

        # Help menu
        h = m.addMenu('&Help')

        about_action = h.addAction('About...')
        about_action.setShortcut('Ctrl+H')
        about_action.triggered.connect(self.handle_about)


    def handle_open(self) -> None:
        """Handle file opening"""
        fp = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '', 'Binary Files (*.bin);;All Files (*)')[0]
        if fp == '': return
        self.file_path = fp

        with open(fp, 'rb') as f:
            data = f.read()

        LevelInfo = LevelInfoFile.from_data(data)
        if LevelInfo is None:
            return

        self.view.set_file(LevelInfo)

        self.save_action.setEnabled(True)

    def handle_save(self) -> None:
        """Handle file saving"""
        data = self.view.save_file()

        with open(self.file_path, 'wb') as f:
            f.write(data)

    def handle_save_as(self) -> None:
        """Handle saving to a new file"""
        fp = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '', 'Binary Files (*.bin);;All Files (*)')[0]
        if fp == '': return
        self.file_path = fp

        self.handle_save()

        self.save_action.setEnabled(True)

    def handle_exit(self) -> None:
        """Exit"""
        self.close()

    def handle_about(self) -> None:
        """Show the About dialog"""
        try:
            with open('readme.md', 'r', encoding='utf-8') as f:
                readme = f.read()
        except Exception:
            readme = 'Level Info Editor {VERSION} by RoadrunnerWMC\n(No readme.md found!)\nLicensed under GPL 3'

        text_edit = QtWidgets.QPlainTextEdit(readme)
        text_edit.setReadOnly(True)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(text_edit)
        layout.addWidget(button_box)

        dlg = QtWidgets.QDialog()
        dlg.setLayout(layout)
        dlg.setModal(True)
        dlg.setMinimumWidth(384)
        button_box.accepted.connect(dlg.accept)
        dlg.exec()



def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())

main()
