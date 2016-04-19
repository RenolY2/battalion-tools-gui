# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bw_gui_prototype.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

import random
import traceback
from copy import copy, deepcopy
from os import path
from timeit import default_timer

from PyQt5 import Qt, QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QColor
from lib.bw_read_xml import BattWarsLevel

ENTITY_SIZE = 10
MODEL_ATTR = {
    "sAirVehicleBase": "model",
    "cObjectiveMarkerBase": "mModel",
    "cBuildingImpBase": "mpModel",
    "cObjectiveMarkerBase": "mModel",
    "sDestroyBase": "Model",
    "sTroopBase": "mBAN_Model",
    "cGroundVehicleBase": "mpModel",
    "sPickupBase": "mModel",
}

COLORS = {
    "cAirVehicle": "yellow",
    "cGroundVehicle": "brown",
    "cTroop": "blue"
}


def bw_coords_to_image_coords(bw_x, bw_y):
    img_x = ((bw_x + (4096//2)) // 2)
    img_y = ((bw_y + (4096//2)) // 2)
    img_y = (4096//2) - img_y

    return img_x, img_y


def image_coords_to_bw_coords(img_x, img_y):
    bw_x = img_x*2 - (4096//2)
    bw_y = (4096//2) - 2*img_y

    #print(img_x, img_y, bw_x, bw_y)

    return bw_x, bw_y

for ix in range(0, 2048+1, 1024):
    for iy in range(0, 2048+1, 1024):
        x, y = image_coords_to_bw_coords(ix, iy)
        print(ix, iy, x, y, bw_coords_to_image_coords(x, y))




def entity_get_model(xml, entityid):
    try:
        entityobj = xml.obj_map[entityid]
        baseobj = xml.obj_map[entityobj.get_attr_value("mBase")]
        modelobj = xml.obj_map[baseobj.get_attr_value(
            MODEL_ATTR[baseobj.type]
        )]

        return modelobj.get_attr_value("mName")
    except:
        traceback.print_exc()
        return None


def entity_get_army(xml, entityid):
    try:
        entityobj = xml.obj_map[entityid]
        baseobj = xml.obj_map[entityobj.get_attr_value("mBase")]

        return baseobj.get_attr_value("mArmy")
    except:
        traceback.print_exc()
        return None


def entity_get_icon_type(xml, entityid):
    try:
        entityobj = xml.obj_map[entityid]
        baseobj = xml.obj_map[entityobj.get_attr_value("mBase")]

        return baseobj.get_attr_value("unitIcon")
    except:
        traceback.print_exc()
        return None


def set_default_path(path):
    print("WRITING", path)
    try:
        with open("default_path.cfg", "wb") as f:
            f.write(bytes(path, encoding="utf-8"))
    except Exception as error:
        print("couldn't write path")
        traceback.print_exc()
        pass


def get_default_path():
    print("READING")
    try:
        with open("default_path.cfg", "rb") as f:
            path = str(f.read(), encoding="utf-8")
        return path
    except:
        return None



def generate_unique_id(xml, id_base):
    base_str = str(id_base)
    prefix = int(base_str[0:2])

    digits = len(base_str)-2
    rest = int(base_str[2:])

    newid = int(id_base)
    newid_str = None
    done = False

    # We keep the first two digits, but choose the remaining digits in such a way that
    # they are unique.
    for i in range(10**digits):
        newid = prefix * (10**digits) + ((rest + 7*i) % (10**digits))
        newid_str = str(newid)

        if newid_str not in xml.obj_map:
            break # We made a new unique object id!

    #print("original id:",id_base)
    #print("new id:", newid_str)
    return newid_str

def object_get_position(xml, entityid):
    obj = xml.obj_map[entityid]

    matr4x4 = [float(x) for x in obj.get_attr_value("Mat").split(",")]
    x, y = matr4x4[12], matr4x4[14]

    return x, y

def object_set_position(xml, entityid, x, y):
    obj = xml.obj_map[entityid]

    matr4x4 = [float(x) for x in obj.get_attr_value("Mat").split(",")]
    matr4x4[12] = x
    matr4x4[14] = y

    obj.set_attr_value("Mat", ",".join(str(x) for x in matr4x4))



class BWMapViewer(QtWidgets.QWidget):
    mouse_clicked = QtCore.pyqtSignal(QtGui.QMouseEvent)
    entity_clicked = QtCore.pyqtSignal(QtGui.QMouseEvent, str)
    mouse_dragged = QtCore.pyqtSignal(QtGui.QMouseEvent)
    mouse_released = QtCore.pyqtSignal(QtGui.QMouseEvent)

    ENTITY_SIZE = ENTITY_SIZE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.zoom_factor = 1

        self.SIZEX = 2048#1024
        self.SIZEY = 2048#1024


        self.setMinimumSize(QtCore.QSize(self.SIZEX, self.SIZEY))
        self.setMaximumSize(QtCore.QSize(self.SIZEX, self.SIZEY))
        self.setObjectName("bw_map_screen")


        self.point_x = 0
        self.point_y = 0

        # This value is used for switching between several entities that overlap.
        self.next_selected_index = 0

        #self.entities = [(0,0, "abc")]
        self.entities = {}#{"abc": (0, 0)}
        self.current_entity = None

    def reset(self):
        del self.entities
        self.entities = {}
        self.current_entity = None

        self.point_x = self.point_y = 0

        self.next_selected_index = 0
        self.zoom_factor = 1

        self.SIZEX = 2048#1024
        self.SIZEY = 2048#1024

        self.setMinimumSize(QtCore.QSize(self.SIZEX, self.SIZEY))
        self.setMaximumSize(QtCore.QSize(self.SIZEX, self.SIZEY))

    def choose_entity(self, entityid):
        self.current_entity = entityid

        self.update()

    def move_entity(self, entityid, x, y):
        # Update the position of an entity
        self.entities[entityid][0] = x
        self.entities[entityid][1] = y

    def add_entities(self, entities):
        for x, y, entityid, entitytype in entities:
            #self.entities.append((x, y, entityid))
            self.entities[entityid] = [x, y, entitytype]

    def remove_entity(self, entityid):
        # If the entity is selected, unselect it before deleting it.
        if self.current_entity is not None:
            if entityid == self.current_entity:
                self.current_entity = None

        del self.entities[entityid]

    def rename_entity(self, oldid, newid):
        # We do not allow renaming an entity to a different name that already exists
        assert newid == oldid or newid not in self.entities

        if newid != oldid:
            self.entities[newid] = copy(self.entities[oldid])
            del self.entities[oldid]
        else:
            pass # Don't need to do anything if the old id is the same as the new id

    def add_entity(self, x, y, entityid, entitytype, update=True):
        #self.entities.append((x, y, random.randint(10, 50)))
        self.entities[entityid] = [x, y, entitytype]

        # In case lots of entities are added at once, update can be set to False to avoid
        # redrawing the widget too much.
        if update:
            self.update()

    def zoom(self, fac):

        if (self.zoom_factor + fac) > 0.1 and (self.zoom_factor + fac) <= 25:
            self.zoom_factor += fac
            self.zoom_factor = round(self.zoom_factor, 2)
            zf = self.zoom_factor
            self.setMinimumSize(QtCore.QSize(self.SIZEX*zf, self.SIZEY*zf))
            self.setMaximumSize(QtCore.QSize(self.SIZEX*zf, self.SIZEY*zf))

    def paintEvent(self, event):
        start = default_timer()

        p = QtGui.QPainter(self)
        p.begin(self)
        h = self.height()
        w = self.width()
        p.setBrush(QtGui.QColor("white"))
        p.drawRect(0, 0, h-1, w-1)
        if self.zoom_factor > 1:
            ENTITY_SIZE = int(self.ENTITY_SIZE * (1 + self.zoom_factor/10.0))
        else:
            ENTITY_SIZE = self.ENTITY_SIZE

        zf = self.zoom_factor
        current_entity = self.current_entity
        last_color = None

        for entity, data in self.entities.items():
            x, y, entitytype = data
            x *= zf
            y *= zf

            if entitytype in COLORS:
                color = COLORS[entitytype]
            else:
                color = "black"
            if last_color != color:
                p.setBrush(QColor(color))
                last_color = color
            if current_entity != entity:
                p.drawRect(x-ENTITY_SIZE//2, y-ENTITY_SIZE//2, ENTITY_SIZE, ENTITY_SIZE)

        # Draw the currently selected entity last so it is always above all other entities.
        if self.current_entity is not None:
            x, y, entitytype = self.entities[self.current_entity]
            x *= self.zoom_factor
            y *= self.zoom_factor

            p.setBrush(QtGui.QColor("red"))

            p.drawRect(x-ENTITY_SIZE//2, y-ENTITY_SIZE//2, ENTITY_SIZE, ENTITY_SIZE)

            p.setBrush(QtGui.QColor("black"))

        p.end()
        end = default_timer()

        print("time taken:", end-start, "sec")

    def mousePressEvent(self, event):
        #x,y = event.localPos()
        #if event.x() < self.height() and event.y() < self.width:

        print(event.x(),event.y())
        event_x, event_y = event.x(), event.y()
        hit = False
        search_start = default_timer()

        if self.zoom_factor > 1:
            ENTITY_SIZE = int(self.ENTITY_SIZE * (1 + self.zoom_factor/10.0))
        else:
            ENTITY_SIZE = self.ENTITY_SIZE

        entities_hit = []

        for entity, data in self.entities.items():
            x, y, entitytype = data
            x *= self.zoom_factor
            y *= self.zoom_factor

            if ((x + ENTITY_SIZE//2) > event_x > (x - ENTITY_SIZE//2)
                    and (y + ENTITY_SIZE//2) > event_y > (y - ENTITY_SIZE//2)):
                #hit = True
                entities_hit.append(entity)

        if len(entities_hit) > 0:
            if self.next_selected_index > (len(entities_hit) - 1):
                self.next_selected_index = 0
            entity = entities_hit[self.next_selected_index]

            search_end = default_timer()
            print("time for search:", search_end-search_start, "sec")
            self.next_selected_index = (self.next_selected_index+1) % len(entities_hit)
            self.entity_clicked.emit(event, entity)
        else:
            self.mouse_clicked.emit(event)

    def mouseMoveEvent(self, event):
        self.mouse_dragged.emit(event)
    def mouseReleaseEvent(self, event):
        self.mouse_released.emit(event)

class BWEntityEntry(QtWidgets.QListWidgetItem):
    def __init__(self, xml_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.xml_ref = xml_ref


class BWEntityListWidget(QtWidgets.QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def select_item(self, pos):
        #item = self.item(pos)
        self.setCurrentRow(pos)


def get_type(typename):
    if typename in ("cGroundVehicle", "cTroop", "cAirVehicle", "cWaterVehicle"):
        return "a"
    else:
        return "b"


class EditorMainWindow(QtWidgets.QMainWindow):
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

        self.moving = False

        self.resetting = False

        self.entity_list_widget.currentItemChanged.connect(self.change_text)
        self.button_zoom_in.pressed.connect(self.zoom_in)
        self.button_zoom_out.pressed.connect(self.zoom_out)
        self.button_remove_entity.pressed.connect(self.remove_position)
        self.button_move_entity.pressed.connect(self.move_entity)
        self.button_clone_entity.pressed.connect(self.action_clone_entity)

        self.bw_map_screen.mouse_clicked.connect(self.get_position)
        self.bw_map_screen.entity_clicked.connect(self.entity_position)
        self.bw_map_screen.mouse_dragged.connect(self.mouse_move)
        self.bw_map_screen.mouse_released.connect(self.mouse_release)

        status = self.statusbar
        self.bw_map_screen.setMouseTracking(True)

    def reset(self):
        self.resetting = True
        self.statusbar.clearMessage()
        self.dragged_time = None
        self.moving = False
        #self.default_path = ""
        print("so far so well")
        self.dragging = False
        self.last_x = None
        self.last_y = None
        self.dragged_time = None

        self.moving = False
        print("good")

        self.entity_list_widget.clearSelection()
        self.entity_list_widget.clear()
        #del self.level
        #self.level = None
        print("list cleared")
        self.bw_map_screen.reset()
        self.resetting = False

    def action_clone_entity(self):
        currentity = self.bw_map_screen.current_entity

        if currentity is not None:
            obj = self.level.obj_map[currentity]
            xml_node = deepcopy(obj._xml_node)
            try:
                cloned_id = generate_unique_id(self.level, currentity)
                xml_node.set("id", cloned_id)
                self.level.add_object(xml_node)

                bw_x, bw_y = object_get_position(self.level, cloned_id)
                print("CURRENT_POSITION", bw_x, bw_y)
                x, y = bw_coords_to_image_coords(bw_x, bw_y)
                print(bw_x, bw_y, (image_coords_to_bw_coords(x, y)))

                self.add_item_sorted(cloned_id)

                self.bw_map_screen.add_entity(x, y, cloned_id, obj.type)

                #self.choose_entity(newid)
                self.bw_map_screen.choose_entity(cloned_id)
                self.set_entity_text(cloned_id)
                print("CREATED:", cloned_id)


                clonedobj = self.level.obj_map[cloned_id]

                if clonedobj.has_attr("mPassenger"):
                    print("COPYING PASSENGERS")
                    orig_x = bw_x
                    orig_y = bw_y
                    passengers = clonedobj.get_attr_elements("mPassenger")

                    passengers_added = []

                    for i, passenger in enumerate(passengers):
                        if passenger != "0":
                            obj = self.level.obj_map[passenger]
                            xml_node = deepcopy(obj._xml_node)

                            clonedpassenger_id = generate_unique_id(self.level, passenger)
                            xml_node.set("id", clonedpassenger_id)
                            print("orig passenger: {0}, new passenger: {1}, alreadyexists: {2}".format(
                                passenger, clonedpassenger_id, clonedpassenger_id in self.level.obj_map
                            ))
                            print(type(passenger), type(clonedpassenger_id))

                            self.level.add_object(xml_node)
                            #x, y = object_get_position(self.level, newid)
                            x = orig_x + (i+1)*8
                            y = orig_y + (i+1)*8
                            print(orig_x, orig_y, x, y)
                            object_set_position(self.level, clonedpassenger_id, x, y)
                            x, y = bw_coords_to_image_coords(x, y)


                            self.add_item_sorted(clonedpassenger_id)
                            #item = BWEntityEntry(newid, "{0}[{1}]".format(newid, obj.type))
                            #self.entity_list_widget.addItem(item)
                            self.bw_map_screen.add_entity(x, y, clonedpassenger_id, obj.type)
                            passengers_added.append(passenger)
                            clonedobj.set_attr_value("mPassenger", clonedpassenger_id, i)
                    print("passengers added:", passengers_added)
                    """if len(passengers_added) > 0:
                        QtWidgets.QMessageBox.information(self, "MessageInfo",
                                                        "The following passengers were added: {0}".format(
                                                            ", ".join(passengers_added)
                                                        )

                        )"""
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
            currstring = get_type(currobj.type)+currobj.type

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

    def move_entity(self):
        if not self.dragging:
            if not self.moving:
                self.moving = True
                currtext = self.button_move_entity.text()
                self.button_move_entity.setText("Stop ["+currtext+"]")
            else:
                self.moving = False

                currtext = self.button_move_entity.text()
                currtext = currtext[6:]
                currtext = currtext.strip("[]")
                self.button_move_entity.setText(currtext)


    """def choose_entity(self, entityid):
        entityobj = self.level.obj_map[entityid]
        self.bw_map_screen.choose_entity(entityid)

        self.label_object_id.setText("ID: {0}".format(entityid))

        self.label_object_id.setText("ID: {0}".format(entityid))"""

    def button_load_level(self):
        try:
            print("ok", self.default_path)
            self.xmlPath = ""
            filepath, choosentype = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open File",
                self.default_path,
                "BW level files (*_level.xml);;All files (*)")
            print("doooone")
            if filepath:
                print("resetting")
                self.reset()
                print("done")

                with open(filepath, "rb") as f:
                    try:
                        self.level = BattWarsLevel(f)
                        self.default_path = filepath
                        set_default_path(filepath)

                        for obj_id, obj in sorted(self.level.obj_map.items(),
                                                  key=lambda x: get_type(x[1].type)+x[1].type+x[1].id):
                            #print("doing", obj_id)
                            if not obj.has_attr("Mat"):
                                continue
                            x, y = object_get_position(self.level, obj_id)
                            x, y = bw_coords_to_image_coords(x, y)

                            item = BWEntityEntry(obj_id, "{0}[{1}]".format(obj_id, obj.type))
                            self.entity_list_widget.addItem(item)

                            self.bw_map_screen.add_entity(x, y, obj_id, obj.type, update=False)
                        print("ok")
                        self.bw_map_screen.update()
                        path_parts = path.split(filepath)
                        self.setWindowTitle("BW-MapEdit - {0}".format(path_parts[-1]))

                    except Exception as error:
                        print("error", error)
                        traceback.print_exc()
        except Exception as er:
            print("errrorrr", error)
            traceback.print_exc()
        print("loaded")

    def button_save_level(self):
        if self.level is not None:
            filepath, choosentype = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save File",
                self.default_path,
                "BW level files (*_level.xml);;All files (*)")
            print(filepath, "saved")
            if filepath:
                with open(filepath, "wb") as f:
                    self.level._tree.write(f)

                self.default_path = filepath
        else:
            pass # no level loaded, do nothing

    def entity_position(self, event, entity):
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
        self.bw_map_screen.update()

    def remove_position(self):
        #self.bw_map_screen.entities.pop()
        current_entity = self.bw_map_screen.current_entity
        if current_entity is not None:
            try:
                # Remove the entity from the map, the list widget and the level data
                pos = self.get_entity_item_pos(current_entity)
                item = self.entity_list_widget.takeItem(pos)
                assert item.xml_ref == current_entity
                self.entity_list_widget.removeItemWidget(item)
                self.level.remove_object(current_entity)
                self.bw_map_screen.remove_entity(current_entity)
                self.bw_map_screen.update()
            except:
                traceback.print_exc()
                raise

    def get_position(self, event):
        self.dragging = True
        self.last_x = event.x()
        self.last_y = event.y()
        self.dragged_time = default_timer()

        x = event.x()/self.bw_map_screen.zoom_factor
        y = event.y()/self.bw_map_screen.zoom_factor

        if not self.moving:
            pass
        else:
            if self.bw_map_screen.current_entity is not None:
                newx, newy = image_coords_to_bw_coords(x, y)
                print("Old position:", object_get_position(self.level, self.bw_map_screen.current_entity))
                object_set_position(self.level, self.bw_map_screen.current_entity,
                                    newx, newy)
                self.bw_map_screen.move_entity(self.bw_map_screen.current_entity,
                                               x, y)
                self.set_entity_text(self.bw_map_screen.current_entity)

                print("New position:", object_get_position(self.level, self.bw_map_screen.current_entity))


        self.bw_map_screen.update()

    def mouse_move(self, event):
        x, y = image_coords_to_bw_coords(event.x()/self.bw_map_screen.zoom_factor,
                                         event.y()/self.bw_map_screen.zoom_factor)
        self.statusbar.showMessage("x: {0} y: {1}".format(x, y))

        if self.dragging and default_timer() - self.dragged_time > 0.1:
            delta_x = (event.x()-self.last_x)/8
            delta_y = (event.y()-self.last_y)/8
            print("hi",event.x(), event.y())

            vertbar = self.scrollArea.verticalScrollBar()
            horizbar = self.scrollArea.horizontalScrollBar()

            vertbar.setSliderPosition(vertbar.value()-delta_y)
            horizbar.setSliderPosition(horizbar.value()-delta_x)

    def mouse_release(self, event):
        self.dragging = False

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
            x, y = object_get_position(self.level, entityid)
            self.label_position.setText("x: {0}\ny: {1}".format(x, y))

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


    def change_text(self, current, previous):
        #QtWidgets.QListWidgetItem.
        if not self.resetting:
            print("ok")
            print("hi", current.text(), current.xml_ref)

            self.set_entity_text(current.xml_ref)
            self.bw_map_screen.choose_entity(current.xml_ref)

            posx, posy, typename = self.bw_map_screen.entities[current.xml_ref]
            zf = self.bw_map_screen.zoom_factor
            try:
                self.scrollArea.ensureVisible(posx*zf, posy*zf,
                                              xMargin=int(50*zf), yMargin=int(50*zf))
            except:
                traceback.print_exc()
    def zoom_out(self):

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
        #zf = self.bw_map_screen.zoom_factor/1.10
        self.bw_map_screen.zoom(-0.2)#diff)
        self.statusbar.showMessage("Zoom: {0}x".format(self.bw_map_screen.zoom_factor))
        horizbar.setSliderPosition(horizbar.maximum()*widthratio)
        vertbar.maximum()
        vertbar.setSliderPosition(vertbar.maximum()*heightratio)

        self.bw_map_screen.update()

    def zoom_in(self):
        horizbar = self.scrollArea.horizontalScrollBar()
        vertbar = self.scrollArea.verticalScrollBar()

        if horizbar.maximum() > 0:
            widthratio = horizbar.value()/horizbar.maximum()
        else:
            widthratio = 0

        if vertbar.maximum() > 0:
            heightratio = vertbar.value()/vertbar.maximum()
        else:
            heightratio = 0#zf = self.bw_map_screen.zoom_factor*0.10
        self.bw_map_screen.zoom(0.2)#zf)
        self.statusbar.showMessage("Zoom: {0}x".format(self.bw_map_screen.zoom_factor))

        print("wedidit?")
        horizbar.setSliderPosition(horizbar.maximum()*widthratio)
        vertbar.setSliderPosition(vertbar.maximum()*heightratio)

        self.bw_map_screen.update()

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(820, 760)
        MainWindow.setMinimumSize(QtCore.QSize(720, 560))
        MainWindow.setWindowTitle("BW-MapEdit")


        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")


        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)

        self.bw_map_screen = BWMapViewer(self.centralwidget)
        self.scrollArea.setWidget(self.bw_map_screen)
        self.horizontalLayout.addWidget(self.scrollArea)

        #self.horizontalLayout.addWidget(self.bw_map_screen)

        self.entity_list_widget = BWEntityListWidget(self.centralwidget)
        self.entity_list_widget.setMaximumSize(QtCore.QSize(300, 16777215))
        self.entity_list_widget.setObjectName("entity_list_widget")
        self.horizontalLayout.addWidget(self.entity_list_widget)

        spacerItem = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout.addItem(spacerItem)

        self.vertLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.vertLayoutWidget.setMaximumSize(QtCore.QSize(200, 600))
        self.verticalLayout = QtWidgets.QVBoxLayout(self.vertLayoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        #self.verticalLayout.
        self.button_clone_entity = QtWidgets.QPushButton(self.centralwidget)
        self.button_clone_entity.setObjectName("button_clone_entity")
        self.verticalLayout.addWidget(self.button_clone_entity)

        self.button_remove_entity = QtWidgets.QPushButton(self.centralwidget)
        self.button_remove_entity.setObjectName("button_remove_entity")
        self.verticalLayout.addWidget(self.button_remove_entity)

        self.button_move_entity = QtWidgets.QPushButton(self.centralwidget)
        self.button_move_entity.setObjectName("button_move_entity")
        self.verticalLayout.addWidget(self.button_move_entity)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.button_zoom_in = QtWidgets.QPushButton(self.centralwidget)
        self.button_zoom_in.setObjectName("button_zoom_in")
        self.gridLayout.addWidget(self.button_zoom_in, 0, 0, 0, 1)

        self.button_zoom_out = QtWidgets.QPushButton(self.centralwidget)
        self.button_zoom_out.setObjectName("button_zoom_out")
        self.gridLayout.addWidget(self.button_zoom_out, 0, 1, 0, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        spacerItem1 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)

        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")


        self.label_object_id = QtWidgets.QLabel(self.centralwidget)
        self.label_object_id.setObjectName("label_object_id")

        self.label_position = QtWidgets.QLabel(self.centralwidget)
        self.label_position.setObjectName("label_position")

        self.label_model_name = QtWidgets.QLabel(self.centralwidget)
        self.label_model_name.setObjectName("label_model_name")

        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")

        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")

        self.verticalLayout_2.addWidget(self.label_object_id)
        self.verticalLayout_2.addWidget(self.label_position)
        self.verticalLayout_2.addWidget(self.label_model_name)
        self.verticalLayout_2.addWidget(self.label_4)
        self.verticalLayout_2.addWidget(self.label_5)

        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.horizontalLayout.addWidget(self.vertLayoutWidget)

        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 820, 29))
        self.menubar.setObjectName("menubar")
        self.file_menu = QtWidgets.QMenu(self.menubar)
        self.file_menu.setObjectName("menuLoad")



        self.file_load_action = QtWidgets.QAction("Load", self)
        self.file_load_action.triggered.connect(self.button_load_level)
        self.file_menu.addAction(self.file_load_action)
        self.file_save_action = QtWidgets.QAction("Save", self)
        self.file_save_action.triggered.connect(self.button_save_level)
        self.file_menu.addAction(self.file_save_action)



        self.menuLoad_2 = QtWidgets.QMenu(self.menubar)
        self.menuLoad_2.setObjectName("menuLoad_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.file_menu.menuAction())
        self.menubar.addAction(self.menuLoad_2.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.button_clone_entity.setText(_translate("MainWindow", "Clone Entity"))
        self.button_remove_entity.setText(_translate("MainWindow", "Delete Entity"))
        self.button_move_entity.setText(_translate("MainWindow", "Move Entity"))
        self.button_zoom_in.setText(_translate("MainWindow", "Zoom In"))
        self.button_zoom_out.setText(_translate("MainWindow", "Zoom Out"))

        self.label_model_name.setText(_translate("MainWindow", "TextLabel1"))
        self.label_object_id.setText(_translate("MainWindow", "TextLabel2"))
        self.label_position.setText(_translate("MainWindow", "TextLabel3"))
        self.label_4.setText(_translate("MainWindow", "TextLabel4"))
        self.label_5.setText(_translate("MainWindow", "TextLabel5"))
        self.file_menu.setTitle(_translate("MainWindow", "File"))

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)


    bw_gui = EditorMainWindow()

    bw_gui.show()
    err_code = app.exec()
    #traceback.print_exc()
    sys.exit(err_code)
