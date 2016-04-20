# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bw_gui_prototype.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

import traceback
from copy import copy, deepcopy
from os import path
from timeit import default_timer

from PyQt5.QtCore import QSize, QRect, QMetaObject, QCoreApplication
from PyQt5.QtWidgets import (QWidget, QMainWindow, QFileDialog,
                             QSpacerItem, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QHBoxLayout,
                             QScrollArea, QGridLayout, QMenuBar, QMenu, QAction, QApplication, QStatusBar)

from lib.bw_read_xml import BattWarsLevel
from custom_widgets import BWEntityEntry, BWEntityListWidget, BWMapViewer

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


def get_type(typename):
    if typename in ("cGroundVehicle", "cTroop", "cAirVehicle", "cWaterVehicle"):
        return "a"
    else:
        return "b"


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
                cloned_id = self.level.generate_unique_id(currentity)
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

                            clonedpassenger_id = self.level.generate_unique_id(passenger)
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
            filepath, choosentype = QFileDialog.getOpenFileName(
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
            filepath, choosentype = QFileDialog.getSaveFileName(
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
        MainWindow.setMinimumSize(QSize(720, 560))
        MainWindow.setWindowTitle("BW-MapEdit")


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
        self.vertLayoutWidget.setMaximumSize(QSize(200, 600))
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

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.button_zoom_in = QPushButton(self.centralwidget)
        self.button_zoom_in.setObjectName("button_zoom_in")
        self.gridLayout.addWidget(self.button_zoom_in, 0, 0, 0, 1)

        self.button_zoom_out = QPushButton(self.centralwidget)
        self.button_zoom_out.setObjectName("button_zoom_out")
        self.gridLayout.addWidget(self.button_zoom_out, 0, 1, 0, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        spacerItem1 = QSpacerItem(10, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")


        self.label_object_id = QLabel(self.centralwidget)
        self.label_object_id.setObjectName("label_object_id")

        self.label_position = QLabel(self.centralwidget)
        self.label_position.setObjectName("label_position")

        self.label_model_name = QLabel(self.centralwidget)
        self.label_model_name.setObjectName("label_model_name")

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")

        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")

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



        self.menuLoad_2 = QMenu(self.menubar)
        self.menuLoad_2.setObjectName("menuLoad_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.file_menu.menuAction())
        self.menubar.addAction(self.menuLoad_2.menuAction())

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
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

    app = QApplication(sys.argv)


    bw_gui = EditorMainWindow()

    bw_gui.show()
    err_code = app.exec()
    #traceback.print_exc()
    sys.exit(err_code)
