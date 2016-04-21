
from timeit import default_timer
from copy import copy

from PyQt5.QtGui import QMouseEvent, QPainter, QColor
from PyQt5.QtWidgets import (QWidget, QListWidget, QListWidgetItem, QDialog,
                            QMdiSubWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton)
from PyQt5.QtCore import QSize, pyqtSignal


ENTITY_SIZE = 10

COLORS = {
    "cAirVehicle": "yellow",
    "cGroundVehicle": "brown",
    "cTroop": "blue"
}


class BWMapViewer(QWidget):
    mouse_clicked = pyqtSignal(QMouseEvent)
    entity_clicked = pyqtSignal(QMouseEvent, str)
    mouse_dragged = pyqtSignal(QMouseEvent)
    mouse_released = pyqtSignal(QMouseEvent)

    ENTITY_SIZE = ENTITY_SIZE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.zoom_factor = 1

        self.SIZEX = 2048#1024
        self.SIZEY = 2048#1024


        self.setMinimumSize(QSize(self.SIZEX, self.SIZEY))
        self.setMaximumSize(QSize(self.SIZEX, self.SIZEY))
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

        self.setMinimumSize(QSize(self.SIZEX, self.SIZEY))
        self.setMaximumSize(QSize(self.SIZEX, self.SIZEY))

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
            #self.zoom_factor = round(self.zoom_factor, 2)
            zf = self.zoom_factor
            self.setMinimumSize(QSize(self.SIZEX*zf, self.SIZEY*zf))
            self.setMaximumSize(QSize(self.SIZEX*zf, self.SIZEY*zf))

    def paintEvent(self, event):
        start = default_timer()

        p = QPainter(self)
        p.begin(self)
        h = self.height()
        w = self.width()
        p.setBrush(QColor("white"))
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
            x *= zf
            y *= zf

            p.setBrush(QColor("red"))

            p.drawRect(x-ENTITY_SIZE//2, y-ENTITY_SIZE//2, ENTITY_SIZE, ENTITY_SIZE)

            p.setBrush(QColor("black"))

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


class BWEntityEntry(QListWidgetItem):
    def __init__(self, xml_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.xml_ref = xml_ref


class BWEntityListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def select_item(self, pos):
        #item = self.item(pos)
        self.setCurrentRow(pos)


class BWPassengerWindow(QMdiSubWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBaseSize(400, 400)
        self.centralwidget = QWidget(self)
        self.setWidget(self.centralwidget)

        layout = QHBoxLayout(self.centralwidget)
        self.passengerlist = QListWidget(self.centralwidget)
        layout.addWidget(self.passengerlist)
        self.setWindowTitle("Passengers")

    def reset(self):
        self.passengerlist.clearSelection()
        self.passengerlist.clear()

    def add_passenger(self, passenger_name, passenger_id):
        item = BWEntityEntry(passenger_id,
                             passenger_name)
        self.passengerlist.addItem(item)

    def set_title(self, entityname):
        self.setWindowTitle("Passengers - {0}".format(entityname))