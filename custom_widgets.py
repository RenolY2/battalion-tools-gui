import traceback
import math
from timeit import default_timer
from copy import copy
import xml.etree.ElementTree as etree

from PyQt5.QtGui import QMouseEvent, QPainter, QColor, QFont, QFontMetrics, QPolygon
from PyQt5.QtWidgets import (QWidget, QListWidget, QListWidgetItem, QDialog, QMenu,
                            QMdiSubWindow, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QTextEdit)
from PyQt5.QtCore import QSize, pyqtSignal, QPoint
from PyQt5.QtCore import Qt


ENTITY_SIZE = 10

COLORS = {
    "cAirVehicle": QColor("yellow"),
    "cGroundVehicle": QColor("brown"),
    "cTroop": QColor("blue"),
    "cMapZone": QColor("grey")
}

MAPZONECOLORS = {
    "ZONETYPE_MISSIONBOUNDARY": QColor("light green")
}
DEFAULT_ENTITY = QColor("black")
DEFAULT_MAPZONE = QColor("grey")
DEFAULT_SELECTED = QColor("red")

class BWMapViewer(QWidget):
    mouse_clicked = pyqtSignal(QMouseEvent)
    entity_clicked = pyqtSignal(QMouseEvent, str)
    mouse_dragged = pyqtSignal(QMouseEvent)
    mouse_released = pyqtSignal(QMouseEvent)

    ENTITY_SIZE = ENTITY_SIZE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._zoom_factor = 10

        self.SIZEX = 2048#1024
        self.SIZEY = 2048#1024


        self.setMinimumSize(QSize(self.SIZEX, self.SIZEY))
        self.setMaximumSize(QSize(self.SIZEX, self.SIZEY))
        self.setObjectName("bw_map_screen")


        self.point_x = 0
        self.point_y = 0
        self.polygon_cache = {}

        # This value is used for switching between several entities that overlap.
        self.next_selected_index = 0

        #self.entities = [(0,0, "abc")]
        self.entities = {}#{"abc": (0, 0)}
        self.current_entity = None
        self.visibility_toggle = {}

    def set_visibility(self, visibility):
        self.visibility_toggle = visibility

    def reset(self):
        del self.entities
        self.entities = {}
        self.current_entity = None

        self.point_x = self.point_y = 0

        self.next_selected_index = 0
        self._zoom_factor = 10
        del self.polygon_cache
        self.polygon_cache = {}
        self.visibility_toggle = {}

        self.SIZEX = 2048#1024
        self.SIZEY = 2048#1024

        self.setMinimumSize(QSize(self.SIZEX, self.SIZEY))
        self.setMaximumSize(QSize(self.SIZEX, self.SIZEY))

    @property
    def zoom_factor(self):
        return self._zoom_factor/10.0

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
            self.entities[entityid] = [x, y, entitytype, None]

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
            if self.current_entity == oldid:
                self.current_entity = newid
            del self.entities[oldid]
            self.update()
        else:
            pass # Don't need to do anything if the old id is the same as the new id

    def add_entity(self, x, y, entityid, entitytype, update=True, metadata=None):
        #self.entities.append((x, y, random.randint(10, 50)))
        self.entities[entityid] = [x, y, entitytype, metadata]

        # In case lots of entities are added at once, update can be set to False to avoid
        # redrawing the widget too much.
        if update:
            self.update()

    def zoom(self, fac):
        if (self.zoom_factor + fac) > 0.1 and (self.zoom_factor + fac) <= 25:
            self._zoom_factor += int(fac*10)
            #self.zoom_factor = round(self.zoom_factor, 2)
            zf = self.zoom_factor
            self.setMinimumSize(QSize(self.SIZEX*zf, self.SIZEY*zf))
            self.setMaximumSize(QSize(self.SIZEX*zf, self.SIZEY*zf))

    def draw_entity(self, painter, x, y, size, zf, entityid, metadata):
        #print(x,y,size, type(x), type(y), type(size), metadata)
        painter.drawRect(x-size//2, y-size//2, size, size)

    def draw_box(self, painter, x, y, size, zf, entityid, metadata, polycache):
        #painter.drawRect(x-size//2, y-size//2, size, size)
        if metadata is not None:
            width = metadata["width"]*zf
            length = metadata["length"]*zf
            #print("drawing")

            if (entityid not in polycache or
                        width != polycache[entityid][1] or length != polycache[entityid][2]
                        or x != polycache[entityid][3] or y != polycache[entityid][4]):
                polygon = QPolygon([QPoint(x-width//2, y-length//2), QPoint(x-width//2, y+length//2),
                                    QPoint(x+width//2, y+length//2), QPoint(x+width//2, y-length//2),
                                    QPoint(x-width//2, y-length//2)])
                polycache[entityid] = [polygon, width, length, x, y]
                pass
            else:
                pass
                polygon = polycache[entityid][0]

            #painter.rotate(45)
            radius = metadata["radius"]*zf
            if radius != 0.0:
                painter.drawArc(x-radius//2, y-radius//2, radius, radius, 0, 16*360)
            painter.drawPolyline(polygon)

            #painter.rotate(-45)

    def set_metadata(self, entityid, metadata):
        self.entities[entityid][3] = metadata

    def paintEvent(self, event):
        start = default_timer()
        #print("painting")

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
        #print("we are good")
        #try:
        drawbox = self.draw_box
        drawentity = self.draw_entity
        polycache = self.polygon_cache
        toggle = self.visibility_toggle
        for entity, data in self.entities.items():
            x, y, entitytype, metadata = data
            x *= zf
            y *= zf

            if entitytype in toggle and toggle[entitytype] is False:
                continue

            if entitytype in COLORS:
                color = COLORS[entitytype]
            else:
                color = DEFAULT_ENTITY
            if last_color != color:
                p.setBrush(color)
                #p.setPen(QColor(color))
                last_color = color
            if current_entity != entity:
                #print(entitytype)
                if entitytype == "cMapZone":
                    mapzonetype = metadata["zonetype"]
                    if mapzonetype in MAPZONECOLORS:
                        color = MAPZONECOLORS[mapzonetype]
                    else:
                        color = DEFAULT_MAPZONE
                    drawentity(p, x, y, ENTITY_SIZE, zf, entity, metadata)

                    pen = p.pen()
                    pen.setColor(color)
                    origwidth = pen.width()
                    pen.setWidth(5)
                    p.setPen(pen)
                    drawbox(p, x, y, ENTITY_SIZE, zf, entity, metadata, polycache)
                    pen.setColor(DEFAULT_ENTITY)
                    pen.setWidth(origwidth)
                    p.setPen(pen)
                else:
                    drawentity(p, x, y, ENTITY_SIZE, zf, entity, metadata)

        # Draw the currently selected entity last so it is always above all other entities.
        if self.current_entity is not None:
            x, y, entitytype, metadata = self.entities[self.current_entity]
            x *= zf
            y *= zf

            p.setBrush(QColor("red"))

            if entitytype == "cMapZone":
                self.draw_entity(p, x, y, ENTITY_SIZE, zf, self.current_entity, metadata)
                pen = p.pen()
                pen.setColor(DEFAULT_SELECTED)
                origwidth = pen.width()
                pen.setWidth(8)
                p.setPen(pen)
                self.draw_box(p, x, y, ENTITY_SIZE, zf, self.current_entity, metadata, polycache)
                pen.setColor(DEFAULT_ENTITY)
                pen.setWidth(origwidth)
                p.setPen(pen)
            else:
                self.draw_entity(p, x, y, ENTITY_SIZE, zf, self.current_entity, metadata)

            p.setBrush(DEFAULT_ENTITY)

        p.end()
        end = default_timer()

        print("time taken:", end-start, "sec")

    def mousePressEvent(self, event):
        #x,y = event.localPos()
        #if event.x() < self.height() and event.y() < self.width:

        print(event.x(), event.y())
        event_x, event_y = event.x(), event.y()
        hit = False
        search_start = default_timer()

        if self.zoom_factor > 1:
            ENTITY_SIZE = int(self.ENTITY_SIZE * (1 + self.zoom_factor/10.0))
        else:
            ENTITY_SIZE = self.ENTITY_SIZE

        entities_hit = []
        toggle = self.visibility_toggle
        for entity, data in self.entities.items():
            x, y, entitytype, metadata = data
            x *= self.zoom_factor
            y *= self.zoom_factor
            if entitytype in toggle and toggle[entitytype] is False:
                continue
            if ((x + ENTITY_SIZE//2) > event_x > (x - ENTITY_SIZE//2)
                and (y + ENTITY_SIZE//2) > event_y > (y - ENTITY_SIZE//2)):
                #hit = True
                entities_hit.append(entity)

        print("we got it")
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

class MenuDontClose(QMenu):
    def mouseReleaseEvent(self, e):
        try:
            action = self.activeAction()
            if action and action.isEnabled():
                action.trigger()
            else:
                QMenu.mouseReleaseEvent(self, e)
        except:
            traceback.print_exc()

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


class BWEntityXMLEditor(QMdiSubWindow):
    def __init__(self, *args, **kwargs):
        if "windowtype" in kwargs:
            self.windowname = kwargs["windowtype"]
            del kwargs["windowtype"]
        else:
            self.windowname = "XML Object"

        super().__init__(*args, **kwargs)



        self.resize(900, 500)
        self.setMinimumSize(QSize(300, 300))

        self.centralwidget = QWidget(self)
        self.setWidget(self.centralwidget)
        self.entity = None

        font = QFont()
        font.setFamily("Consolas")
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        font.setPointSize(10)

        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.textbox_xml = QTextEdit(self.centralwidget)
        self.button_xml_savetext = QPushButton(self.centralwidget)
        self.button_xml_savetext.setText("Save XML")
        self.button_xml_savetext.setMaximumWidth(400)
        self.textbox_xml.setLineWrapMode(QTextEdit.NoWrap)

        metrics = QFontMetrics(font)
        self.textbox_xml.setTabStopWidth(4 * metrics.width(' '))
        self.textbox_xml.setFont(font)

        self.verticalLayout.addWidget(self.textbox_xml)
        self.verticalLayout.addWidget(self.button_xml_savetext)
        self.setWindowTitle(self.windowname)

    def set_content(self, xmlnode):
        try:
            self.textbox_xml.setText(etree.tostring(xmlnode, encoding="unicode"))
            self.entity = xmlnode.get("id")
        except:
            traceback.print_exc()

    def get_content(self):
        try:
            content = self.textbox_xml.toPlainText()
            xmlnode = etree.fromstring(content)

            return xmlnode
        except:
            traceback.print_exc()

    def set_title(self, objectname):
        self.setWindowTitle("{0} - {1}".format(self.windowname, objectname))

    def reset(self):
        pass