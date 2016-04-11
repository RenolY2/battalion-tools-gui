# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bw_gui_prototype.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

import random
from PyQt5 import Qt, QtCore, QtGui, QtWidgets

class BWMapViewer(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setMinimumSize(QtCore.QSize(512, 512))
        self.setMaximumWidth(512)
        self.setObjectName("bw_map_screen")


    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.begin(self)
        h = self.height()
        w = self.width()
        p.setBrush(QtGui.QColor("white"))
        p.drawRect(0, 0, h, w)




        p.end()
        """
        for i in range(1, h, h/5):
            p.setPen(QtGui.QColor("lightgray"))
            p.drawLine(0, i, w, i)
        """

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

        for i in range(100):
            item = BWEntityEntry(random.randint(0, 100), "Item {0}".format(i))
            self.entity_list_widget.addItem(item)

        self.entity_list_widget.currentItemChanged.connect(self.change_text)
        self.pushButton_2.pressed.connect(self.next_item)

    def change_text(self, current, previous):
        #QtWidgets.QListWidgetItem.
        print("hi", current.text(), current.xml_ref)
        self.label.setText(str(current.xml_ref))

        self.label_2.setText(str(current.xml_ref+random.randint(10,50)))
        pass

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

        self.bw_map_screen = BWMapViewer(self.centralwidget)

        self.horizontalLayout.addWidget(self.bw_map_screen)

        self.entity_list_widget = BWEntityListWidget(self.centralwidget)
        self.entity_list_widget.setMaximumSize(QtCore.QSize(400, 16777215))
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
        self.menuLoad = QtWidgets.QMenu(self.menubar)
        self.menuLoad.setObjectName("menuLoad")
        self.menuLoad_2 = QtWidgets.QMenu(self.menubar)
        self.menuLoad_2.setObjectName("menuLoad_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuLoad.menuAction())
        self.menubar.addAction(self.menuLoad_2.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.pushButton_4.setText(_translate("MainWindow", "Clone Entity"))
        self.pushButton_5.setText(_translate("MainWindow", "Delete Entity"))
        self.pushButton_2.setText(_translate("MainWindow", "Increment"))
        self.pushButton_3.setText(_translate("MainWindow", "PushButton 1"))
        self.label.setText(_translate("MainWindow", "TextLabel1"))
        self.label_2.setText(_translate("MainWindow", "TextLabel2"))
        self.label_3.setText(_translate("MainWindow", "TextLabel3"))
        self.label_4.setText(_translate("MainWindow", "TextLabel4"))
        self.label_5.setText(_translate("MainWindow", "TextLabel5"))
        self.menuLoad.setTitle(_translate("MainWindow", "Save"))
        self.menuLoad_2.setTitle(_translate("MainWindow", "Load"))

if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QMainWindow

    app = QtWidgets.QApplication(sys.argv)


    bw_gui = EditorMainWindow()

    bw_gui.show()

    sys.exit(app.exec())
