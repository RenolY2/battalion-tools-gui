# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bw_gui_prototype.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

import traceback
import itertools
import gzip
from copy import copy, deepcopy
import os
from os import path
from timeit import default_timer
from math import atan2, degrees, radians, sin, cos

from PyQt5.QtCore import QSize, QRect, QMetaObject, QCoreApplication, QPoint
from PyQt5.QtWidgets import (QWidget, QMainWindow, QFileDialog,
                             QSpacerItem, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QGridLayout, QMenuBar, QMenu, QAction, QApplication, QStatusBar, QLineEdit)
from PyQt5.QtGui import QMouseEvent
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore

from res_tools.bw_archive_base import BWArchiveBase

from lib.bw_read_xml import BattWarsLevel, BattWarsObject
from custom_widgets import (BWEntityEntry, BWEntityListWidget, BWMapViewer, BWPassengerWindow, BWEntityXMLEditor, MenuDontClose,
                            catch_exception,
                            SHOW_TERRAIN_LIGHT, SHOW_TERRAIN_NO_TERRAIN, SHOW_TERRAIN_REGULAR)


from lib.helper_functions import (calc_zoom_in_factor, calc_zoom_out_factor,
                                  get_default_path, set_default_path, update_mapscreen,
                                  bw_coords_to_image_coords, image_coords_to_bw_coords,
                                  entity_get_army, entity_get_icon_type, entity_get_model,
                                  object_set_position, object_get_position, get_position_attribute, get_type,
                                  parse_terrain_to_image, get_water_height)

BW_LEVEL = "BW level files (*_level.xml *_level.xml.gz)"
BW_COMPRESSED_LEVEL = "BW compressed level files (*_level.xml.gz)"

class EditorMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.retranslateUi(self)

        self.level = None
        path = get_default_path()
        if path is None:
            self.default_path = ""
        else:
            self.default_path = path

        self.dragging = False
        self.last_x = None
        self.last_y = None
        self.dragged_time = None
        self.deleting_item = False # Hack for preventing focusing on next item after deleting the previous one

        self.moving = False

        self.resetting = False

        self.entity_list_widget.currentItemChanged.connect(self.action_listwidget_change_selection)
        self.button_zoom_in.pressed.connect(self.zoom_in)
        self.button_zoom_out.pressed.connect(self.zoom_out)
        self.button_remove_entity.pressed.connect(self.remove_position)
        self.button_move_entity.pressed.connect(self.move_entity)
        self.button_clone_entity.pressed.connect(self.action_clone_entity)
        self.button_show_passengers.pressed.connect(self.action_passenger_window)
        self.button_edit_xml.pressed.connect(self.action_open_xml_editor)
        self.button_edit_base_xml.pressed.connect(self.action_open_basexml_editor)
        self.lineedit_angle.editingFinished.connect(self.action_lineedit_changeangle)


        self.bw_map_screen.mouse_clicked.connect(self.get_position)
        self.bw_map_screen.entity_clicked.connect(self.entity_position)
        self.bw_map_screen.mouse_dragged.connect(self.mouse_move)
        self.bw_map_screen.mouse_released.connect(self.mouse_release)
        self.bw_map_screen.mouse_wheel.connect(self.mouse_wheel_scroll_zoom)


        status = self.statusbar
        self.bw_map_screen.setMouseTracking(True)

        self.passenger_window = BWPassengerWindow()
        self.passenger_window.passengerlist.currentItemChanged.connect(self.passengerwindow_action_choose_entity)

        self.xmlobject_textbox = BWEntityXMLEditor()
        self.xmlobject_textbox.button_xml_savetext.pressed.connect(self.xmleditor_action_save_object_xml)
        self.xmlobject_textbox.triggered.connect(self.action_open_xml_editor_unlimited)


        self.basexmlobject_textbox = BWEntityXMLEditor(windowtype="XML Base Object")
        self.basexmlobject_textbox.button_xml_savetext.pressed.connect(self.xmleditor_action_save_base_object_xml)
        self.basexmlobject_textbox.triggered.connect(self.action_open_xml_editor_unlimited)

        self.types_visible = {}
        self.terrain_image = None

        status.showMessage("Ready")

        self.xml_windows = {}
        print("We are now ready!")

    def reset(self):
        self.resetting = True
        self.statusbar.clearMessage()
        self.dragged_time = None
        self.moving = False
        self.dragging = False
        self.last_x = None
        self.last_y = None
        self.dragged_time = None

        self.moving = False

        self.entity_list_widget.clearSelection()
        self.entity_list_widget.clear()

        self.bw_map_screen.reset()
        self.clear_visibility_toggles()

        for window in (self.passenger_window, self.xmlobject_textbox, self.basexmlobject_textbox):
            window.close()
            window.reset()

        for id in self.xml_windows:
            self.destroy_xml_editor(id)

        self.resetting = False

        print("reset done")

    def destroy_xml_editor(self, id):
        pass

    @catch_exception
    def open_xml_editor(self, objectid, offsetx=0, offsety=0):
        selected = objectid
        if self.level is not None and selected in self.level.obj_map:
            delete = []
            for objid, window in self.xml_windows.items():
                if not window.isVisible() and objid != selected:
                    window.destroy()
                    delete.append(objid)
            for objid in delete:
                del self.xml_windows[objid]

            if selected == self.basexmlobject_textbox.entity or selected == self.xmlobject_textbox.entity:
                pass # No need to make a new window
            elif selected in self.xml_windows and self.xml_windows[selected].isVisible():
                self.xml_windows[selected].activateWindow()
                self.xml_windows[selected].update()

            else:
                xml_window = BWEntityXMLEditor()

                def xmleditor_save_object_unlimited():
                    self.statusbar.showMessage("Saving object changes...")
                    try:
                        xmlnode = xml_window.get_content()
                        #assert self.bw_map_screen.current_entity == self.basexmlobject_textbox.entity
                        assert xml_window.entity == xmlnode.get("id")  # Disallow changing the id of the base object

                        self.level.remove_object(xmlnode.get("id"))
                        self.level.add_object(xmlnode)

                        self.statusbar.showMessage("Saved base object {0} as {1}".format(
                            xml_window.entity, self.level.obj_map[xmlnode.get("id")].name))
                    except:
                        self.statusbar.showMessage("Saving object failed")
                        traceback.print_exc()

                xml_window.button_xml_savetext.pressed.connect(xmleditor_save_object_unlimited)
                xml_window.triggered.connect(self.action_open_xml_editor_unlimited)


                obj = self.level.obj_map[selected]
                xml_window.set_title(obj.name)

                xml_window.set_content(obj._xml_node)
                #xml_window.move(QPoint(xml_editor_owner.pos().x()+20, xml_editor_owner.pos().y()+20))
                xml_window.move(QPoint(offsetx, offsety))

                xml_window.show()
                xml_window.update()
                self.xml_windows[selected] = xml_window



    @catch_exception
    def action_open_xml_editor_unlimited(self, xml_editor_owner):
        selected = xml_editor_owner.textbox_xml.textCursor().selectedText()
        self.open_xml_editor(selected,
                             offsetx=xml_editor_owner.pos().x()+20,
                             offsety=xml_editor_owner.pos().y()+20)

    @catch_exception
    def action_open_basexml_editor(self):
        """
        if not self.basexmlobject_textbox.isVisible():
            self.basexmlobject_textbox.destroy()
            self.basexmlobject_textbox = BWEntityXMLEditor(windowtype="XML Base Object")
            self.basexmlobject_textbox.button_xml_savetext.pressed.connect(self.xmleditor_action_save_base_object_xml)
            self.basexmlobject_textbox.triggered.connect(self.action_open_xml_editor_unlimited)
            self.basexmlobject_textbox.show()

        self.basexmlobject_textbox.activateWindow()"""
        if self.level is not None and self.bw_map_screen.current_entity is not None:
            obj = self.level.obj_map[self.bw_map_screen.current_entity]
            if not obj.has_attr("mBase"):
                pass
            else:
                baseobj = self.level.obj_map[obj.get_attr_value("mBase")]
                #self.basexmlobject_textbox.set_title(baseobj.id)
                self.open_xml_editor(baseobj.id)

    def xmleditor_action_save_base_object_xml(self):
        self.statusbar.showMessage("Saving base object changes...")
        try:
            xmlnode = self.basexmlobject_textbox.get_content()
            #assert self.bw_map_screen.current_entity == self.basexmlobject_textbox.entity
            assert self.basexmlobject_textbox.entity == xmlnode.get("id")  # Disallow changing the id of the base object

            self.level.remove_object(xmlnode.get("id"))
            self.level.add_object(xmlnode)

            self.statusbar.showMessage("Saved base object {0} as {1}".format(
                self.basexmlobject_textbox.entity, self.level.obj_map[xmlnode.get("id")].name))
        except:
            self.statusbar.showMessage("Saving base object failed")
            traceback.print_exc()

    def action_open_xml_editor(self):
        """
        if not self.xmlobject_textbox.isVisible():
            self.xmlobject_textbox.destroy()
            self.xmlobject_textbox = BWEntityXMLEditor()
            self.xmlobject_textbox.button_xml_savetext.pressed.connect(self.xmleditor_action_save_object_xml)
            self.xmlobject_textbox.triggered.connect(self.action_open_xml_editor_unlimited)
            self.xmlobject_textbox.show()

        self.xmlobject_textbox.activateWindow()"""
        if self.level is not None and self.bw_map_screen.current_entity is not None:
            entityobj = self.level.obj_map[self.bw_map_screen.current_entity]
            self.open_xml_editor(objectid=entityobj.id)

            update_mapscreen(self.bw_map_screen, self.level.obj_map[entityobj.id])
            self.bw_map_screen.update()

        """self.xmlobject_textbox.set_title(entityobj.id)

            self.xmlobject_textbox.set_content(entityobj._xml_node)

            self.xmlobject_textbox.update()"""

    def xmleditor_action_save_object_xml(self):
        self.statusbar.showMessage("Saving object changes...")
        try:
            xmlnode = self.xmlobject_textbox.get_content()
            #assert self.bw_map_screen.current_entity == self.xmlobject_textbox.entity
            assert self.xmlobject_textbox.entity == xmlnode.get("id") or xmlnode.get("id") not in self.level.obj_map

            if self.passenger_window.isVisible():
                self.passenger_window.close()

            if self.xmlobject_textbox.entity != xmlnode.get("id"):
                #obj = self.level.obj_map[xmlnode.get("id")]
                self.level.remove_object(self.xmlobject_textbox.entity)
                print("adding", xmlnode.get("id"), xmlnode.get("id") in self.level.obj_map )
                self.level.add_object(xmlnode)

                pos = self.get_entity_item_pos(self.xmlobject_textbox.entity)
                item = self.entity_list_widget.takeItem(pos)
                self.entity_list_widget.removeItemWidget(item)
                self.add_item_sorted(xmlnode.get("id"))

                self.bw_map_screen.rename_entity(self.xmlobject_textbox.entity, xmlnode.get("id"))
                assert xmlnode.get("id") in self.level.obj_map
                self.xmlobject_textbox.entity = xmlnode.get("id")
                self.xmlobject_textbox.set_title(xmlnode.get("id"))

            else:
                self.level.remove_object(xmlnode.get("id"))
                self.level.add_object(xmlnode)

            update_mapscreen(self.bw_map_screen, self.level.obj_map[xmlnode.get("id")])

            self.statusbar.showMessage("Saved object {0} as {1}".format(
                self.xmlobject_textbox.entity, self.level.obj_map[xmlnode.get("id")].name))
            self.bw_map_screen.update()

        except:
            self.statusbar.showMessage("Saving object failed")
            traceback.print_exc()

    def action_clone_entity(self):
        entities = []
        if self.bw_map_screen.current_entity is not None:
            entities.append(self.bw_map_screen.current_entity)
        elif len(self.bw_map_screen.selected_entities) > 0:
            entities.extend(self.bw_map_screen.selected_entities.keys())

        if len(entities) > 0:
            dont_clone = {}
            for entity in entities:
                obj = self.level.obj_map[entity]
                if obj.has_attr("mPassenger"):
                    passengers = obj.get_attr_elements("mPassenger")
                    for passenger in passengers:
                        if passenger != "0":
                            dont_clone[passenger] = True
            select = []
            for entity in entities:
                if entity in dont_clone:
                    continue

                obj = self.level.obj_map[entity]

                xml_node = deepcopy(obj._xml_node)
                try:
                    cloned_id = self.level.generate_unique_id(entity)
                    xml_node.set("id", cloned_id)
                    self.level.add_object(xml_node)

                    bw_x, bw_y, angle = object_get_position(self.level, cloned_id)
                    x, y = bw_coords_to_image_coords(bw_x, bw_y)

                    self.add_item_sorted(cloned_id)

                    self.bw_map_screen.add_entity(x, y, cloned_id, obj.type)

                    clonedobj = self.level.obj_map[cloned_id]
                    select.append(cloned_id)
                    update_mapscreen(self.bw_map_screen, clonedobj)
                    if clonedobj.has_attr("mPassenger"):
                        orig_x = bw_x
                        orig_y = bw_y
                        passengers = clonedobj.get_attr_elements("mPassenger")

                        passengers_added = []

                        for i, passenger in enumerate(passengers):
                            if passenger != "0":
                                obj = self.level.obj_map[passenger]
                                xml_node = deepcopy(obj._xml_node)

                                clonedpassenger_id = self.level.generate_unique_id(passenger)
                                xml_node.set("id", clonedpassenger_id)
                                #print("orig passenger: {0}, new passenger: {1}, alreadyexists: {2}".format(
                                #    passenger, clonedpassenger_id, clonedpassenger_id in self.level.obj_map
                                #))
                                #print(type(passenger), type(clonedpassenger_id))

                                self.level.add_object(xml_node)
                                #x, y = object_get_position(self.level, newid)
                                x = orig_x + (i+1)*8
                                y = orig_y + (i+1)*8
                                #print(orig_x, orig_y, x, y)
                                object_set_position(self.level, clonedpassenger_id, x, y)
                                x, y = bw_coords_to_image_coords(x, y)

                                self.add_item_sorted(clonedpassenger_id)
                                self.bw_map_screen.add_entity(x, y, clonedpassenger_id, obj.type)
                                update_mapscreen(self.bw_map_screen, self.level.obj_map[clonedpassenger_id])
                                passengers_added.append(passenger)
                                clonedobj.set_attr_value("mPassenger", clonedpassenger_id, i)
                                select.append(clonedpassenger_id)
                        #print("passengers added:", passengers_added)
                    self.bw_map_screen.selected_entities = {}
                    if len(select) == 1:
                        ent = select[0]
                        self.set_entity_text(ent)
                        self.bw_map_screen.choose_entity(ent)
                    else:
                        for ent in select:
                            self.bw_map_screen.selected_entities[ent] = True
                        self.set_entity_text_multiple(self.bw_map_screen.selected_entities)
                    self.bw_map_screen.update()
                except:
                    traceback.print_exc()

    def add_item_sorted(self, entity):
        max_count = self.entity_list_widget.count()
        entityobj = self.level.obj_map[entity]
        index = 0
        entity_item = BWEntityEntry(entity, "{0}[{1}]".format(entity, entityobj.type))

        # Similar to loading a level, we add the entity in a sorted way by
        # creating this string and comparing it for every item in the list.
        entity_string = get_type(entityobj.type)+entityobj.type+entityobj.id

        inserted = False

        for i in range(max_count):
            curritem = self.entity_list_widget.item(i)
            currobj = self.level.obj_map[curritem.xml_ref]
            currstring = get_type(currobj.type)+currobj.type+currobj.id

            # The list is already sorted, so if we find an item bigger than
            # the one we are inserting, we know the position we have to insert the item in.
            # String comparison should be alpabetically.
            if currstring > entity_string:
                self.entity_list_widget.insertItem(i, entity_item)
                inserted = True
                break

        # If we couldn't insert the item, i.e. there are no items at all
        # or all items are smaller than the item we add, we just add it at the end.
        if not inserted:
            self.entity_list_widget.addItem(entity_item)

    def get_entity_item_pos(self, entityid):
        for i in range(self.entity_list_widget.count()):
            item = self.entity_list_widget.item(i)

            if item.xml_ref == entityid:
                return i

        return None

    def action_passenger_window(self):
        #if self.passenger_window.isVisible()
        print("window is visible: ", self.passenger_window.isVisible())
        #self.passenger_window.reset()

        if not self.passenger_window.isVisible():
            self.passenger_window.destroy()
            self.passenger_window = BWPassengerWindow()
            self.passenger_window.passengerlist.currentItemChanged.connect(self.passengerwindow_action_choose_entity)
            self.passenger_window.show()

        self.passenger_window.activateWindow()
        if self.bw_map_screen.current_entity is not None:
            self.passenger_window.reset()
            entityobj = self.level.obj_map[self.bw_map_screen.current_entity]
            self.passenger_window.set_title(entityobj.id)
            if entityobj.has_attr("mPassenger"):
                for i, passenger in enumerate(entityobj.get_attr_elements("mPassenger")):
                    if passenger in self.level.obj_map:
                        passengerobj = self.level.obj_map[passenger]
                        list_item_name = "{0}[{1}]".format(passenger, passengerobj.type)
                    elif passenger == "0":
                        list_item_name = "{0}<none>".format(passenger)
                    else:
                        list_item_name = "{0}<missing>".format(passenger)
                    self.passenger_window.add_passenger(list_item_name, passenger)
            self.passenger_window.update()

    def passengerwindow_action_choose_entity(self, current, previous):
        try:
            if current is not None and current.xml_ref in self.level.obj_map:
                self.set_entity_text(current.xml_ref)
                self.bw_map_screen.choose_entity(current.xml_ref)
            elif current is not None:
                self.statusbar.showMessage("No such entity: {0}".format(current.xml_ref), 1000*2)
        except:
            traceback.print_exc()

    def move_entity(self):
        if not self.dragging:
            if not self.moving:
                self.moving = True
                currtext = self.button_move_entity.text()
                self.button_move_entity.setText("Stop [Move Entity]")
            else:
                self.moving = False

                currtext = "Move Entity"
                self.button_move_entity.setText(currtext)

    def button_load_level(self):
        try:
            print("ok", self.default_path)
            self.xmlPath = ""
            filepath, choosentype = QFileDialog.getOpenFileName(
                self, "Open File",
                self.default_path,
                BW_LEVEL+";;"+BW_COMPRESSED_LEVEL+";;All files (*)")
            print("doooone")
            if filepath:
                print("resetting")
                self.reset()
                print("done")
                print("chosen type:",choosentype)

                # Some BW levels are clear XML files, some are compressed with GZIP
                # We decide between the two either based on user choice or end of filepath
                if choosentype == BW_COMPRESSED_LEVEL or filepath.endswith(".gz"):
                    print("OPENING AS COMPRESSED")
                    file_open = gzip.open
                else:
                    file_open = open

                with file_open(filepath, "rb") as f:
                    try:
                        self.level = BattWarsLevel(f)
                        self.default_path = filepath
                        set_default_path(filepath)

                        self.setup_visibility_toggles()

                        for obj_id, obj in sorted(self.level.obj_map.items(),
                                                  key=lambda x: get_type(x[1].type)+x[1].type+x[1].id):
                            #print("doing", obj_id)
                            if get_position_attribute(obj) is None:
                                continue
                            #if not obj.has_attr("Mat"):
                            #    continue
                            x, y, angle = object_get_position(self.level, obj_id)
                            assert type(x) != str
                            x, y = bw_coords_to_image_coords(x, y)

                            item = BWEntityEntry(obj_id, "{0}[{1}]".format(obj_id, obj.type))
                            self.entity_list_widget.addItem(item)

                            self.bw_map_screen.add_entity(x, y, obj_id, obj.type, update=False)
                            #if obj.type == "cMapZone":
                            update_mapscreen(self.bw_map_screen, obj)

                        print("ok")
                        self.bw_map_screen.update()
                        path_parts = path.split(filepath)
                        self.setWindowTitle("BW-MapEdit - {0}".format(path_parts[-1]))

                    except Exception as error:
                        print("error", error)
                        traceback.print_exc()
        except Exception as er:
            print("errrorrr", er)
            traceback.print_exc()
        print("loaded")

    def button_save_level(self):
        if self.level is not None:
            filepath, choosentype = QFileDialog.getSaveFileName(
                self, "Save File",
                self.default_path,
                BW_LEVEL+";;"+BW_COMPRESSED_LEVEL+";;All files (*)")
            print(filepath, "saved")

            if filepath:
                # Simiar to load level
                if choosentype == BW_COMPRESSED_LEVEL or filepath.endswith(".gz"):
                    file_open = gzip.open
                else:
                    file_open = open
                try:
                    with file_open(filepath, "wb") as f:
                        self.level._tree.write(f)
                except Exception as error:
                    print("COULDN'T SAVE:", error)
                    traceback.print_exc()

                self.default_path = filepath
        else:
            pass # no level loaded, do nothing

    def entity_position(self, event, entity):
        try:
            # Make it possible to select objects in move mode, but don't make it too easy to lose
            # a selection.
            if not (self.moving and len(self.bw_map_screen.selected_entities) > 1):
                print("got entity:",entity, self.bw_map_screen.entities[entity][2])
                print(entity_get_model(self.level, entity))
                self.set_entity_text(entity)
                self.bw_map_screen.choose_entity(entity)
                pos = self.get_entity_item_pos(entity)
                print("searching:",pos)
                try:
                    self.entity_list_widget.select_item(pos)
                except:
                    traceback.print_exc()
                self.bw_map_screen.selected_entities = {}

                self.bw_map_screen.update()

        except:
            traceback.print_exc()

    def remove_position(self):
        #self.bw_map_screen.entities.pop()
        try:
            # Remove the entity from the map, the list widget and the level data
            self.deleting_item = True
            entities = []
            if self.bw_map_screen.current_entity is not None:
                entities.append(self.bw_map_screen.current_entity)
            elif len(self.bw_map_screen.selected_entities) > 0:
                entities.extend(self.bw_map_screen.selected_entities.keys())
                self.bw_map_screen.selected_entities = {}
                self.set_entity_text_multiple(self.bw_map_screen.selected_entities)
            if len(entities) > 0:
                for entity in entities:
                    pos = self.get_entity_item_pos(entity)
                    item = self.entity_list_widget.takeItem(pos)
                    assert item.xml_ref == entity
                    #self.entity_list_widget.clearSelection()
                    self.entity_list_widget.clearFocus()
                    self.entity_list_widget.removeItemWidget(item)
                    self.level.remove_object(entity)
                    self.bw_map_screen.remove_entity(entity)

                self.bw_map_screen.update()
        except:
            traceback.print_exc()
            raise

    #@catch_exception
    def get_position(self, event):
        self.dragging = True
        self.last_x = event.x()
        self.last_y = event.y()
        self.dragged_time = default_timer()

        mouse_x = event.x()/self.bw_map_screen.zoom_factor
        mouse_y = event.y()/self.bw_map_screen.zoom_factor

        if event.buttons() == QtCore.Qt.LeftButton:

            if not self.moving:
                self.bw_map_screen.set_selectionbox_start((event.x(), event.y()))
            else:
                if self.bw_map_screen.current_entity is not None:
                    newx, newy = image_coords_to_bw_coords(mouse_x, mouse_y)
                    object_set_position(self.level, self.bw_map_screen.current_entity,
                                        newx, newy)
                    self.bw_map_screen.move_entity(self.bw_map_screen.current_entity,
                                                   mouse_x, mouse_y)
                    self.set_entity_text(self.bw_map_screen.current_entity)

                    update_mapscreen(self.bw_map_screen, self.level.obj_map[self.bw_map_screen.current_entity])

                elif len(self.bw_map_screen.selected_entities) > 0:
                    for entity in self.bw_map_screen.selected_entities:
                        first_entity = entity
                        break
                    #first_entity = self.bw_map_screen.selected_entities.keys()[0]
                    x, y, entitytype, metadata = self.bw_map_screen.entities[first_entity]
                    startx = endx = x
                    starty = endy = y

                    for entity in self.bw_map_screen.selected_entities:
                        x, y, dontneed, dontneed = self.bw_map_screen.entities[entity]
                        if x < startx:
                            startx = x
                        if x > endx:
                            endx = x
                        if y < starty:
                            starty = y
                        if y > endy:
                            endy = y
                    middle_x = (startx+endx) / 2
                    middle_y = (starty+endy) / 2

                    delta_x = mouse_x - middle_x
                    delta_y = mouse_y - middle_y

                    for entity in self.bw_map_screen.selected_entities:
                        x, y, dontneed, dontneed = self.bw_map_screen.entities[entity]

                        newx, newy = image_coords_to_bw_coords(x+delta_x, y+delta_y)
                        object_set_position(self.level, entity,
                                            newx, newy)
                        self.bw_map_screen.move_entity(entity,
                                                       x+delta_x, y+delta_y)
                        #self.set_entity_text(self.bw_map_screen.current_entity)

                        update_mapscreen(self.bw_map_screen, self.level.obj_map[entity])

            self.bw_map_screen.update()

    @catch_exception
    def mouse_move(self, event):
        x, y = image_coords_to_bw_coords(event.x()/self.bw_map_screen.zoom_factor,
                                         event.y()/self.bw_map_screen.zoom_factor)
        self.statusbar.showMessage("x: {0} y: {1}".format(round(x, 5), round(y, 5)))

        if self.dragging and default_timer() - self.dragged_time > 0.1:
            if event.buttons() == QtCore.Qt.RightButton:
                delta_x = (event.x()-self.last_x)/8
                delta_y = (event.y()-self.last_y)/8
                #print("hi",event.x(), event.y())

                vertbar = self.scrollArea.verticalScrollBar()
                horizbar = self.scrollArea.horizontalScrollBar()

                vertbar.setSliderPosition(vertbar.value()-delta_y)
                horizbar.setSliderPosition(horizbar.value()-delta_x)

            elif event.buttons() == QtCore.Qt.LeftButton:
                self.bw_map_screen.set_selectionbox_end((event.x(), event.y()))
                if len(self.bw_map_screen.selected_entities) > 0 or self.bw_map_screen.current_entity is None:
                    self.bw_map_screen.choose_entity(None)
                    self.set_entity_text_multiple(self.bw_map_screen.selected_entities)
                self.bw_map_screen.update()

    def mouse_release(self, event):
        self.dragging = False
        if self.bw_map_screen.selectionbox_end is not None:
            self.bw_map_screen.clear_selection_box()
            self.bw_map_screen.update()

    def set_entity_text_multiple(self, entities):
        self.label_object_id.setText("{0} objects selected".format(len(entities)))
        MAX = 15
        listentities = [self.level.obj_map[x].name for x in sorted(entities.keys())][0:MAX]
        listentities.sort()
        if len(entities) > MAX:
            listentities.append("... and {0} more".format(len(entities) - len(listentities)))
        self.label_position.setText("\n".join(listentities[:5]))
        self.label_model_name.setText("\n".join(listentities[5:10]))
        self.label_4.setText("\n".join(listentities[10:]))#15]))
        self.label_5.setText("")#("\n".join(listentities[12:16]))

    def set_entity_text(self, entityid):
        try:
            obj = self.level.obj_map[entityid]
            if obj.has_attr("mBase"):
                base = self.level.obj_map[obj.get_attr_value("mBase")]
                self.label_object_id.setText("{0}\n[{1}]\nBase: {2}\n[{3}]".format(
                    entityid, obj.type, base.id, base.type))
            else:
                self.label_object_id.setText("{0}\n[{1}]".format(entityid, obj.type))
            self.label_model_name.setText("Model: {0}".format(entity_get_model(self.level, entityid)))
            x, y, angle = object_get_position(self.level, entityid)
            self.label_position.setText("x: {0}\ny: {1}".format(x, y))
            self.lineedit_angle.setText(str(round(angle,2)))
            self.label_4.setText("Army: {0}".format(entity_get_army(self.level, entityid)))
            if not obj.has_attr("mPassenger"):
                self.label_5.setText("Icon Type: \n{0}".format(entity_get_icon_type(self.level, entityid)))
            else:

                passengers = 0
                for passenger in obj.get_attr_elements("mPassenger"):
                    if passenger != "0":
                        passengers += 1
                self.label_5.setText("Icon Type: \n{0}\n\nPassengers: {1}".format(
                    entity_get_icon_type(self.level, entityid), passengers))
        except:
            traceback.print_exc()

    def action_listwidget_change_selection(self, current, previous):
        #QtWidgets.QListWidgetItem.
        if not self.resetting and current is not None:
            print("ok")
            print("hi", current.text(), current.xml_ref)

            self.set_entity_text(current.xml_ref)
            self.bw_map_screen.choose_entity(current.xml_ref)

            posx, posy, typename, metadata = self.bw_map_screen.entities[current.xml_ref]
            zf = self.bw_map_screen.zoom_factor
            try:
                if not self.deleting_item:
                    x_margin = min(100, 50*zf)
                    y_margin = min(100, 50*zf)
                    self.scrollArea.ensureVisible(posx*zf, posy*zf,
                                                  xMargin=x_margin, yMargin=y_margin)
                else:
                    self.deleting_item = False
            except:
                traceback.print_exc()

    def zoom_out(self, noslider=False):

        horizbar = self.scrollArea.horizontalScrollBar()
        vertbar = self.scrollArea.verticalScrollBar()

        print(horizbar.maximum(), vertbar.maximum())

        if horizbar.maximum() > 0:
            widthratio = horizbar.value()/horizbar.maximum()
        else:
            widthratio = 0

        if vertbar.maximum() > 0:
            heightratio = vertbar.value()/vertbar.maximum()
        else:
            heightratio = 0

        #oldzf = self.bw_map_screen.zoom_factor / (0.1+1)
        #diff = oldzf - self.bw_map_screen.zoom_factor
        zf = self.bw_map_screen.zoom_factor
        self.bw_map_screen.zoom(calc_zoom_out_factor(zf))#diff)

        #
        if not noslider:
            horizbar.setSliderPosition(horizbar.maximum()*widthratio)
            vertbar.setSliderPosition(vertbar.maximum()*heightratio)
            self.bw_map_screen.update()

        self.statusbar.showMessage("Zoom: {0}x".format(self.bw_map_screen.zoom_factor))

    def zoom_in(self, noslider=False):
        horizbar = self.scrollArea.horizontalScrollBar()
        vertbar = self.scrollArea.verticalScrollBar()

        if horizbar.maximum() > 0:
            widthratio = horizbar.value()/horizbar.maximum()
        else:
            widthratio = 0

        if vertbar.maximum() > 0:
            heightratio = vertbar.value()/vertbar.maximum()
        else:
            heightratio = 0

        zf = self.bw_map_screen.zoom_factor
        self.bw_map_screen.zoom(calc_zoom_in_factor(zf))#zf)

        #

        print("wedidit?")
        if not noslider:
            horizbar.setSliderPosition(horizbar.maximum()*widthratio)
            vertbar.setSliderPosition(vertbar.maximum()*heightratio)
            self.bw_map_screen.update()

        self.statusbar.showMessage("Zoom: {0}x".format(self.bw_map_screen.zoom_factor))

    @catch_exception
    def mouse_wheel_scroll_zoom(self, wheel_event):
        print("scrolling", wheel_event)
        print("Scroll", wheel_event.x(), wheel_event.y(), wheel_event.angleDelta().y())#, wheel_event.delta())

        wheel_delta = wheel_event.angleDelta().y()
        zf = self.bw_map_screen.zoom_factor
        norm_x = wheel_event.x()/zf
        norm_y = wheel_event.y()/zf
        if wheel_delta > 0:
            if zf <= 10:
                self.zoom_in(True)

                zf = self.bw_map_screen.zoom_factor

                xmargin = self.scrollArea.viewport().width()//2 - 200
                ymargin = self.scrollArea.viewport().height()//2 - 200
                self.scrollArea.ensureVisible(norm_x*zf, norm_y*zf, xmargin, ymargin)
                self.bw_map_screen.update()
            else:
                self.zoom_in()
        elif wheel_delta < 0:
            self.zoom_out()



    def action_lineedit_changeangle(self):
        if not self.resetting and self.bw_map_screen.current_entity is not None:
            print("ok")
            current = self.bw_map_screen.current_entity
            currx, curry, angle = object_get_position(self.level, current)

            newangle = self.lineedit_angle.text().strip()
            print(newangle, newangle.isdecimal())
            try:
                angle = float(newangle)
                object_set_position(self.level, current, currx, curry, angle=angle)
                currentobj = self.level.obj_map[current]
                update_mapscreen(self.bw_map_screen, currentobj)
                self.bw_map_screen.update()
            except:
                traceback.print_exc()

    def button_terrain_load_action(self):
        try:
            print("ok", self.default_path)
            filepath, choosentype = QFileDialog.getOpenFileName(
                self, "Open File",
                self.default_path,
                "BW terrain files (*.out *out.gz);;All files (*)")
            print("doooone")
            if filepath:
                if filepath.endswith(".gz"):
                    file_open = gzip.open
                else:
                    file_open = open

                with file_open(filepath, "rb") as f:
                    try:
                        terrain = BWArchiveBase(f)
                        if self.level is not None:
                            waterheight = get_water_height(self.level)
                        else:
                            waterheight = None

                        image, light_image = parse_terrain_to_image(terrain, waterheight)
                        self.bw_map_screen.set_terrain(image, light_image)
                    except:
                        traceback.print_exc()
        except:
            traceback.print_exc()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(820, 760)
        MainWindow.setMinimumSize(QSize(720, 560))
        MainWindow.setWindowTitle("BW-MapEdit")
        #MainWindow.setWindowTitle("Nep-Nep")


        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")


        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)

        self.bw_map_screen = BWMapViewer(self.centralwidget)
        self.scrollArea.setWidget(self.bw_map_screen)
        self.horizontalLayout.addWidget(self.scrollArea)

        #self.horizontalLayout.addWidget(self.bw_map_screen)

        self.entity_list_widget = BWEntityListWidget(self.centralwidget)
        self.entity_list_widget.setMaximumSize(QSize(300, 16777215))
        self.entity_list_widget.setObjectName("entity_list_widget")
        self.horizontalLayout.addWidget(self.entity_list_widget)

        spacerItem = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.horizontalLayout.addItem(spacerItem)

        self.vertLayoutWidget = QWidget(self.centralwidget)
        self.vertLayoutWidget.setMaximumSize(QSize(250, 1200))
        self.verticalLayout = QVBoxLayout(self.vertLayoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        #self.verticalLayout.
        self.button_clone_entity = QPushButton(self.centralwidget)
        self.button_clone_entity.setObjectName("button_clone_entity")
        self.verticalLayout.addWidget(self.button_clone_entity)

        self.button_remove_entity = QPushButton(self.centralwidget)
        self.button_remove_entity.setObjectName("button_remove_entity")
        self.verticalLayout.addWidget(self.button_remove_entity)

        self.button_move_entity = QPushButton(self.centralwidget)
        self.button_move_entity.setObjectName("button_move_entity")
        self.verticalLayout.addWidget(self.button_move_entity)

        self.button_show_passengers = QPushButton(self.centralwidget)
        self.button_show_passengers.setObjectName("button_move_entity")
        self.verticalLayout.addWidget(self.button_show_passengers)


        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.button_zoom_in = QPushButton(self.centralwidget)
        self.button_zoom_in.setObjectName("button_zoom_in")
        self.gridLayout.addWidget(self.button_zoom_in, 0, 0, 0, 1)

        self.button_zoom_out = QPushButton(self.centralwidget)
        self.button_zoom_out.setObjectName("button_zoom_out")
        self.gridLayout.addWidget(self.button_zoom_out, 0, 1, 0, 1)

        self.button_edit_xml = QPushButton(self.centralwidget)
        self.button_edit_xml.setObjectName("button_edit_xml")

        self.button_edit_base_xml = QPushButton(self.centralwidget)
        self.button_edit_base_xml.setObjectName("button_edit_base_xml")


        self.verticalLayout.addLayout(self.gridLayout)
        self.verticalLayout.addWidget(self.button_edit_xml)
        self.verticalLayout.addWidget(self.button_edit_base_xml)

        spacerItem1 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")


        self.lineedit_angle = QLineEdit(self.centralwidget)
        self.lineedit_angle.setObjectName("lineedit_angle")
        self.lineedit_angle.setPlaceholderText("Angle")

        self.label_object_id = QLabel(self.centralwidget)
        self.label_object_id.setObjectName("label_object_id")
         #TextSelectableByCursor

        self.label_position = QLabel(self.centralwidget)
        self.label_position.setObjectName("label_position")

        self.label_model_name = QLabel(self.centralwidget)
        self.label_model_name.setObjectName("label_model_name")

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")

        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")

        for label in (self.label_object_id, self.label_position, self.label_model_name, self.label_4, self.label_5):
            label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self.verticalLayout_2.addWidget(self.lineedit_angle)
        self.verticalLayout_2.addWidget(self.label_object_id)
        self.verticalLayout_2.addWidget(self.label_position)
        self.verticalLayout_2.addWidget(self.label_model_name)
        self.verticalLayout_2.addWidget(self.label_4)
        self.verticalLayout_2.addWidget(self.label_5)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.horizontalLayout.addWidget(self.vertLayoutWidget)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 820, 29))
        self.menubar.setObjectName("menubar")
        self.file_menu = QMenu(self.menubar)
        self.file_menu.setObjectName("menuLoad")



        self.file_load_action = QAction("Load", self)
        self.file_load_action.triggered.connect(self.button_load_level)
        self.file_menu.addAction(self.file_load_action)
        self.file_save_action = QAction("Save", self)
        self.file_save_action.triggered.connect(self.button_save_level)
        self.file_menu.addAction(self.file_save_action)

        self.visibility_menu = MenuDontClose(self.menubar)#QMenu(self.menubar)
        self.visibility_menu.setObjectName("visibility")



        #self.visibility_menu.addAction(self.toggle_action)
        self.visibility_actions = []

        self.terrain_menu = QMenu(self.menubar)
        self.terrain_menu.setObjectName("terrain")

        self.terrain_load_action = QAction("Load Terrain", self)
        self.terrain_load_action.triggered.connect(self.button_terrain_load_action)
        self.terrain_menu.addAction(self.terrain_load_action)
        self.terrain_display_actions = []
        self.setup_terrain_display_toggles()

        #self.menuLoad_2 = QMenu(self.menubar)
        #self.menuLoad_2.setObjectName("menuLoad_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.file_menu.menuAction())
        #self.menubar.addAction(self.menuLoad_2.menuAction())
        self.menubar.addAction(self.visibility_menu.menuAction())
        self.menubar.addAction(self.terrain_menu.menuAction())
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)


    def make_terrain_toggle(self, show_mode):
        def terraintoggle(toggled):
            print("I am", show_mode, "and I was pressed")
            if toggled is True:
                for action, toggle, mode in self.terrain_display_actions:
                    if mode != show_mode:
                        action.setChecked(False)
                self.bw_map_screen.set_show_terrain_mode(show_mode)
            elif toggled is False:
                self.bw_map_screen.set_show_terrain_mode(SHOW_TERRAIN_NO_TERRAIN)
            else:
                print("This shouldn't be possible", toggled, type(toggled))
            self.bw_map_screen.update()
        return terraintoggle

    def setup_terrain_display_toggles(self):
        for mode, name in ((SHOW_TERRAIN_REGULAR, "Show Heightmap"),
                            (SHOW_TERRAIN_LIGHT, "Show Lightmap")):
            toggle = self.make_terrain_toggle(mode)
            toggle_action = QAction(name, self)
            toggle_action.setCheckable(True)
            if mode == SHOW_TERRAIN_REGULAR:
                toggle_action.setChecked(True)
            else:
                toggle_action.setChecked(False)
            toggle_action.triggered.connect(toggle)
            self.terrain_menu.addAction(toggle_action)
            self.terrain_display_actions.append((toggle_action, toggle, mode))

    def clear_terrain_toggles(self):
        try:
            for action, func, mode in self.terrain_display_actions:
                self.terrain_menu.removeAction(action)
            self.terrain_display_actions = []
        except:
            traceback.print_exc()

    def make_toggle_function(self, objtype):
        def toggle(toggled):
            print("i was pressed")
            my_type = copy(objtype)
            self.types_visible[my_type] = toggled
            self.bw_map_screen.set_visibility(self.types_visible)
            self.bw_map_screen.update()
        return toggle

    def setup_visibility_toggles(self):
        for objtype in sorted(self.level.objtypes_with_positions):

            toggle = self.make_toggle_function(objtype)


            toggle_action = QAction(copy(objtype), self)
            toggle_action.setCheckable(True)
            toggle_action.setChecked(True)
            toggle_action.triggered.connect(toggle)
            self.types_visible[objtype] = True

            self.visibility_menu.addAction(toggle_action)
            self.visibility_actions.append((toggle_action, toggle))

        toggle_all = QAction("Toggle All", self)
        toggle_all.triggered.connect(self.toggle_visiblity_all)

        self.visibility_menu.addAction(toggle_all)
        self.visibility_actions.append((toggle_all, self.toggle_visiblity_all))

    def toggle_visiblity_all(self):
        for action, func in self.visibility_actions:
            if action.isCheckable():
                objtype = action.text()
                toggle = self.types_visible[objtype]
                self.types_visible[objtype] = not toggle
                action.setChecked(not toggle)
                self.bw_map_screen.set_visibility(self.types_visible)
        self.bw_map_screen.update()

    def clear_visibility_toggles(self):
        try:
            for action, func in self.visibility_actions:
                self.visibility_menu.removeAction(action)
            self.visibility_actions = []
            self.types_visible = {}
        except:
            traceback.print_exc()

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        self.button_clone_entity.setText(_translate("MainWindow", "Clone Entity"))
        self.button_remove_entity.setText(_translate("MainWindow", "Delete Entity"))
        self.button_move_entity.setText(_translate("MainWindow", "Move Entity"))
        self.button_zoom_in.setText(_translate("MainWindow", "Zoom In"))
        self.button_zoom_out.setText(_translate("MainWindow", "Zoom Out"))
        self.button_show_passengers.setText(_translate("MainWindow", "Show Passengers"))
        self.button_edit_xml.setText("Edit Object XML")
        self.button_edit_base_xml.setText("Edit Base Object XML")

        self.label_model_name.setText(_translate("MainWindow", "TextLabel1"))
        self.label_object_id.setText(_translate("MainWindow", "TextLabel2"))
        self.label_position.setText(_translate("MainWindow", "TextLabel3"))
        self.label_4.setText(_translate("MainWindow", "TextLabel4"))
        self.label_5.setText(_translate("MainWindow", "TextLabel5"))
        self.file_menu.setTitle(_translate("MainWindow", "File"))
        self.visibility_menu.setTitle(_translate("MainWindow", "Visibility"))
        self.terrain_menu.setTitle("Terrain")

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)


    bw_gui = EditorMainWindow()

    bw_gui.show()
    err_code = app.exec()
    #traceback.print_exc()
    sys.exit(err_code)
