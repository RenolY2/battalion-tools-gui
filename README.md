# battalion-tools-gui

battalion-tools-gui will be a collection of various GUI tools for working 
with files from the Battalion Wars (GC) and the Battalion Wars 2 (Wii) games.

As of now, the repository has two tools

# bw_gui_proto.py
bw_gui_proto.py is a tool for editing _Level.xml files.
More specifically, it makes it possible to move, delete or clone existing entities
that have a "mPos" attribute. Entities with a "mPassenger" attribute, like vehicles
and helicopters, will have their passengers cloned too, and it is possible to check
the passengers of an entity, if it has any passengers.

The cloning process includes generating a new unique ID for the new entities
to avoid overlap with existing entities.

Moving the level view around is possible by clicking and dragging the mouse on the level view.

# strings_editor.py
strings_editor.py is a tool for viewing/editing .str files of BW1 and BW2. Those files contain strings
used in the main menu, levels and other places in the game. The tool can edit existing messages
or add new messages to the end of the file. Messages at the end of the file can also be deleted.

Adding/removing messages in the middle of the file is not supported, because this would mess with
the indices of existing files, resulting in wrong messages being shown in the game.
You can edit the audio file name and path of a message and the content. The message content
will automatically be encoded in the right format. You can also modify the time for how long
a message will be played, shown by the number with the decimal point.

After modifying a message, be sure to press "Set Message Content" or your changes will be lost.
When you are done modifying the strings file, make sure to save it with File->Save.




# Requirements
* Python 3.X (Windows users should get Python 3.4 to make setting up PyQt 5 easier)
* PyQt 5 (any version should work, but make sure that your version of pyqt 5 supports the version of python you use) 

# Links
* Python 3 can be found here: https://www.python.org/downloads/
* PyQt 5 Windows binaries: https://sourceforge.net/projects/pyqt/files/PyQt5/ (recommended: PyQt-5.5.1)

