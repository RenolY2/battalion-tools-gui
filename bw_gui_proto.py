# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bw_gui_prototype.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

import random
import traceback
from timeit import default_timer

from PyQt5 import Qt, QtCore, QtGui, QtWidgets

from lib.bw_read_xml import BattWarsLevel

ENTITY_SIZE = 10

class BWMapViewer(QtWidgets.QWidget):
    mouse_clicked = QtCore.pyqtSignal(QtGui.QMouseEvent)
    entity_clicked = QtCore.pyqtSignal(QtGui.QMouseEvent, str)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        SIZEX = 1024
        SIZEY = 1024


        self.setMinimumSize(QtCore.QSize(SIZEX, SIZEY))
        self.setMaximumSize(QtCore.QSize(SIZEX, SIZEY))
        self.setObjectName("bw_map_screen")


        self.point_x = 0
        self.point_y = 0

        #self.entities = [(0,0, "abc")]
        self.entities = {"abc": (0, 0)}
        self.current_entity = None

    def choose_entity(self, entityid):
        self.current_entity = entityid

        self.update()

    def add_entities(self, entities):
        for x, y, entityid in entities:
            #self.entities.append((x, y, entityid))
            self.entities[entityid] = (x, y)

    def remove_entity(self, entityid):
        # If the entity is selected, unselect it before deleting it.
        if self.current_entity is not None:
            if entityid == self.current_entity:
                self.current_entity = None

        del self.entities[entityid]


    def add_entity(self, x, y, entityid):
        #self.entities.append((x, y, random.randint(10, 50)))
        self.entities[entityid] = (x, y)
        self.update()

    def paintEvent(self, event):
        start = default_timer()
        p = QtGui.QPainter(self)
        p.begin(self)
        h = self.height()
        w = self.width()
        p.setBrush(QtGui.QColor("white"))
        p.drawRect(0, 0, h-1, w-1)


        p.setBrush(QtGui.QColor("black"))
        for entity, position in self.entities.items():
            x, y = position

            if self.current_entity != entity:
                p.drawRect(x-ENTITY_SIZE//2, y-ENTITY_SIZE//2, ENTITY_SIZE, ENTITY_SIZE)

        # Draw the currently selected entity last so it is always above all other entities.
        if self.current_entity is not None:
            x, y = self.entities[self.current_entity]
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
        for entity, position in self.entities.items():
            x, y = position

            if (event_x > (x - ENTITY_SIZE//2) and event_x < (x + ENTITY_SIZE//2)
                and event_y > (y - ENTITY_SIZE//2) and event_y < (y + ENTITY_SIZE//2)):
                hit = True
                search_end = default_timer()
                print("time for search:", search_end-search_start, "sec")
                self.entity_clicked.emit(event, entity)

        if hit is False:
            self.mouse_clicked.emit(event)


class BWEntityEntry(QtWidgets.QListWidgetItem):
    def __init__(self, xml_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.xml_ref = xml_ref


class BWEntityListWidget(QtWidgets.QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def select_item(self, pos):
        #item = self.item(pos)
        self.setCurrentIndex(pos)


class EditorMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.retranslateUi(self)

        self.level = None
        self.default_path = ""


        for i in range(100):
            item = BWEntityEntry(random.randint(0, 100), "Item {0}".format(i))
            self.entity_list_widget.addItem(item)

        self.entity_list_widget.currentItemChanged.connect(self.change_text)
        self.pushButton_2.pressed.connect(self.next_item)
        self.pushButton_3.pressed.connect(self.remove_position)

        self.bw_map_screen.mouse_clicked.connect(self.get_position)
        self.bw_map_screen.entity_clicked.connect(self.entity_position)

    def button_load_level(self):
        self.xmlPath = ""
        filepath, choosentype = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File",
            self.default_path,
            "BW level files (*_level.xml);;All files (*)")

        if filepath:
            with open(filepath, "rb") as f:
                try:
                    self.level = BattWarsLevel(f)
                    self.default_path = filepath
                except Exception as error:
                    print("error", error)
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
        print("got entity:",entity)
        self.label_5.setText("Entity:{0}".format(entity))
        self.bw_map_screen.choose_entity(entity)

    def remove_position(self):
        #self.bw_map_screen.entities.pop()
        current_entity = self.bw_map_screen.current_entity
        if current_entity  is not None:
            self.bw_map_screen.remove_entity(current_entity)
            self.bw_map_screen.update()

    def get_position(self, event):
        self.label_4.setText("x: {0} y: {1}".format(event.x(), event.y()))

        name = str(random.randint(0, 100000))
        while name in self.bw_map_screen.entities:
            name = str(random.randint(0, 100000))

        self.bw_map_screen.add_entity(event.x(), event.y(), name)
        self.bw_map_screen.choose_entity(name)

    def change_text(self, current, previous):
        #QtWidgets.QListWidgetItem.
        print("hi", current.text(), current.xml_ref)
        self.label.setText(str(current.xml_ref))

        self.label_2.setText(str(current.xml_ref+random.randint(10,50)))

        num = int(current.text().split(" ")[1])

        name = [k for k in self.bw_map_screen.entities.keys()][num]

        self.bw_map_screen.choose_entity(name)

        posx, posy = self.bw_map_screen.entities[name]
        self.scrollArea.ensureVisible(posx, posy)

    def next_item(self):
        print("pressed")
        itemcount = self.entity_list_widget.count()
        curr_pos = self.entity_list_widget.currentRow()
        print(itemcount, curr_pos)
        #self.entity_list_widget.select_item(curr_pos+1 % itemcount)
        self.entity_list_widget.setCurrentRow((curr_pos+7) % itemcount)
        pass

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
        self.entity_list_widget.setMaximumSize(QtCore.QSize(200, 16777215))
        self.entity_list_widget.setObjectName("entity_list_widget")
        self.horizontalLayout.addWidget(self.entity_list_widget)

        spacerItem = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.horizontalLayout.addItem(spacerItem)

        self.vertLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.vertLayoutWidget.setMaximumSize(QtCore.QSize(200, 600))
        self.verticalLayout = QtWidgets.QVBoxLayout(self.vertLayoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        #self.verticalLayout.
        self.pushButton_4 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_4.setObjectName("pushButton_4")
        self.verticalLayout.addWidget(self.pushButton_4)

        self.pushButton_5 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_5.setObjectName("pushButton_5")
        self.verticalLayout.addWidget(self.pushButton_5)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout.addWidget(self.pushButton_2, 1, 0, 1, 1)

        self.pushButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_3.setObjectName("pushButton_3")
        self.gridLayout.addWidget(self.pushButton_3, 0, 0, 1, 1)

        self.verticalLayout.addLayout(self.gridLayout)

        spacerItem1 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)

        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")



        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_2.addWidget(self.label_4)
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_2.addWidget(self.label_5)
        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.horizontalLayout.addWidget(self.vertLayoutWidget)
        #self.horizontalLayout.addLayout(self.verticalLayout)


        #MainWindow.setLayout(self.horizontalLayout)

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
        self.pushButton_4.setText(_translate("MainWindow", "Clone Entity"))
        self.pushButton_5.setText(_translate("MainWindow", "Delete Entity"))
        self.pushButton_2.setText(_translate("MainWindow", "Increment"))
        self.pushButton_3.setText(_translate("MainWindow", "Undo"))
        self.label.setText(_translate("MainWindow", "TextLabel1"))
        self.label_2.setText(_translate("MainWindow", "TextLabel2"))
        self.label_3.setText(_translate("MainWindow", "TextLabel3"))
        self.label_4.setText(_translate("MainWindow", "TextLabel4"))
        self.label_5.setText(_translate("MainWindow", "TextLabel5"))
        self.file_menu.setTitle(_translate("MainWindow", "File"))
        #self.menuLoad_2.setTitle(_translate("MainWindow", "Load"))

if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QMainWindow

    app = QtWidgets.QApplication(sys.argv)


    bw_gui = EditorMainWindow()

    bw_gui.show()

    sys.exit(app.exec())
