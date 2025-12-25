# CHON

CHON is a Python-based logic puzzle computer game with elements 
of chemistry. However, knowledge of chemistry in NOT required.

## Get CHON
### From binaries
Download the provided binaries for your system. CHON can directly be 
executed. No install required.

### From source
Requirements:
* Python >= 3.8
* Kivy >= 2.2.0

Download or clone this repository. Run chon.py.

## Playing
Complete molecules by connecting atoms and molecule fragments until all 
free electrons are paired!

Molecules consist of atoms and bonds. Up to 
three bonds are allowed between two atoms. 

Incomplete molecules also have got atoms with free electrons rotating 
around the atom. 

The number of free electrons is shown for each atom. 

Free electrons can 
form a bond when paired with free electrons of atoms of other 
incomplete molecules. Combine two or more incomplete molecules to pair 
their free electrons by placement of the respective atoms next to each 
other. 

Complete molecules are converted into points and will be removed 
from the reactor. 

### Atoms, electrons and bonds:
There are 4 types of atoms in the game:
* Hydrogen (H): 1 electron
* Oxygen (O): 2 electrons
* Nitrogen (N): 3 electrons
* Carbon (C): 4 electrons

### Take in account:
* If you place two atoms with free electrons next to each other, 
then the max possible number of bonds is formed.
* Once a connection is created, it will remain as it is. You can't split 
a bond anymore.
* Omit to leave free electrons at positions where they can not be
reached anymore.

### Scores:
There are three ways to get points:
* Drop atoms/fragments
* Complete a molecule
* Get bonus by completion a molecule which equals the bonus molecule

Good luck!

TODO

## License
### Software
See LICENSE.

### Assets
All sounds and images provided in this repository are either not eligible
to copyright or granted to free use as 
[CC0](https://creativecommons.org/publicdomain/zero/1.0/legalcode).

Fonts used in this game are free to use under the following conditions:
* [Font OpenArrow by Heeyeun : MIT license](/inc/LICENSE.OpenArrow.md) from 
https://github.com/yeun/open-arrow/
* [Font Segment14 by Paul Flo Williams: OFL License](/inc/LICENSE.segment14.md) 

