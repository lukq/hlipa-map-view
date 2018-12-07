This program allows you to explore the Hlipa game map.

Hlipa is a game for 8-bit computer Sharp MZ-800 (there are also releases of the game for
PMD-85 and Atari ST computers). The game was designed and developed by Karel Šuhajda. In the game a
player controls a character named Hlipa who has infiltrated an enemy complex and must find and destroy
six enemies in the shape of crowns, who are located somewhere in the complex.

The enemy complex is quite large, comprising 255 different rooms. Therefore, to kill all six enemies, having a map will help you in planning your route through the complex.

## Description of program working

One way to create a map would be to play the game inside an emulator and make screenshots of all the
rooms visited. This project uses a different approach - computer memory snapshot is taken in an
emulator of Sharp MZ-800 and the memory contents is analysed to find the location and format of the
room descriptions. A program is then written that decodes the room description data and renders the
rooms on screen, using graphics also decoded from the memory snapshot.

Each room is made of 1024 voxels. The voxels are organised in a grid of 8 (width) times 8 (length)
times 16 (height). Each voxel can be either empty or filled with one of 15 available types of tiles.

The room descriptions in the game data contain instructions how the grid should be filled in with
tiles. The room descriptions use three different instructions. One instruction, taking
arguments for start coordinates and length, leads to a line of tiles being filled in the grid.
The second instruction, taking arguments for start coordinates and two lengths, leads to a rectangle
of tiles being filled in the grid. The third instruction enables using instructions of another room in
the current room. By using the third instruction to share the same tiles in several rooms the game
saves memory space.

The program processes the instructions of each room to fill in the voxel grid, then draws the voxels
back to front.

## Running the program

The program requires Python 3, with Tcl/Tk 8.6 or better. If you don't have Python already installed,
download it from www.python.org/downloads and install it.

Then, open command prompt in the directory of the Hlipa map viewer project, and run the following
command (replace path_to_python with the real path on your computer):

    path_to_python\python hlipamap.py

When the program runs, it shows all game rooms that are on the same floor. To view a different floor,
press keys Home or End, or use the on-screen buttons.

You can also toggle between color rendering and shades of grey rendering by pressing the c key.
