# battalion-tools-gui

battalion-tools-gui will be a collection of various GUI tools for working 
with files from the Battalion Wars (GC) and the Battalion Wars 2 (Wii) games.

As of now, the repository has two tools

# bw_level_edit.py
bw_level_edit.py is a tool for editing _Level.xml files.
More specifically, it makes it possible to move, delete or clone existing entities
that have a "mPos" attribute. Entities with a "mPassenger" attribute, like vehicles
and helicopters, will have their passengers cloned too, and it is possible to check
the passengers of an entity, if it has any passengers.

The cloning process includes generating a new unique ID for the new entities
to avoid overlap with existing entities.

Moving the level view around is possible by holding the right mouse button and dragging
the mouse on the level view. Holding the left mouse button and dragging the mouse around
selects multiple entities, multiple entities can be cloned, moved around or deleted.

You can load the terrain file for a BW level (terrain files end with .out) separately. This
will draw the terrain in the background in a top-down view, making it easier for you to visualize
the level. You can toggle between the Heightmap view and Lightmap view, or disable terrain drawing
by pressing on the view that is currently enabled. If you load the terrain after loading a level,
a water layer will be layed over the terrain based on the level's water height.

You can toggle drawing specific types of entities under "Visibility". This allows for a better overview
of the level and also improves drawing performance because less entities are drawn by the editor.
Hidden entities cannot be clicked on in the level view, and will be ignored when selecting multiple
entities, but you can still select them by clicking on the entity in the list to the right.

## Heightmap view
The Heightmap view colorizes the height of the terrain based on this transition:
Light blue are the very low parts of the terrain. Hues of green are the standard ground level,
with yellow and brown (brown being higher) becoming higher and more mountainous. Grey and white
are very high, with white being the top parts of the terrain.

## Lightmap view
This visualizes the backed lightning. For the most part, it is used mostly for shadows in the
terrain, though in some maps it also used for light from light sources, e.g. lamps.



# strings_editor.py
strings_editor.py is a tool for viewing/editing .str files of BW1 and BW2. Those files contain strings
used in the main menu, levels and other places in the game. The tool can edit existing messages
or add new messages to the end of the file. Messages at the end of the file can also be deleted.

Adding/removing messages in the middle of the file is not supported, because this would mess with
the indices of existing messages, resulting in wrong messages being shown in the game.
You can edit the audio file name and path of a message and the content. The message content
will automatically be encoded in the right format. You can also modify the time for how long
a message will be played, shown by the number with the decimal point.

After modifying a message, be sure to press "Set Message Content" or your changes will be lost.
When you are done modifying the strings file, make sure to save it with File->Save.




# Requirements
* Python 3.X (The editor has been tested with Python 3.4 and Python 3.5)
* PyQt 5 (Make sure that your chosen version of PyQt 5 supports your Python version, e.g. PyQt-5.5.1 for Py3.4 and PyQt-5.6 for Py3.5)

# Links
* Python 3 can be found here: https://www.python.org/downloads/
* PyQt 5 Windows binaries: https://sourceforge.net/projects/pyqt/files/PyQt5/

