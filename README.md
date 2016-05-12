# battalion-tools-gui

battalion-tools-gui will be a collection of various GUI tools for working 
with files from the Battalion Wars (GC) and the Battalion Wars 2 (Wii) games.

At the moment, there is only one tool, bw_gui_proto.py, which is a tool for 
editing _Level.xml files. More specifically, it makes it possible to move, delete
or clone existing entities that have a "mPos" attribute. Entities with a "mPassenger"
attribute, like vehicles and helicopters, will have their passengers cloned too,
and it is possible to check the passengers of an entity, if it has any passengers.

The cloning process includes generating a new unique ID for the new entities
to avoid overlap with existing entities.

Moving the level view around is possible by clicking and dragging the mouse on the level view. 


# Requirements
* Python 3.X (Windows users should get Python 3.4 to make setting up PyQt 5 easier)
* PyQt 5 (any version should work, but make sure that your version of pyqt 5 supports the version of python you use) 

# Links
* Python 3 can be found here: https://www.python.org/downloads/
* PyQt 5 Windows binaries: https://sourceforge.net/projects/pyqt/files/PyQt5/ (recommended: PyQt-5.5.1)

