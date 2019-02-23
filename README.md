# Qt-based GUI for some simple OpenPathSampling simulations

This includes some GUI tools for running some simple simulations with
OpenPathSampling. The overall approach is that one GUI app will help create
input files for OPS (initial trajectory, TPS, and committor simulations, all
with arbitrary number of states), and a second app will provide common
analysis tools. Many of those analysis tools will be relevant for TIS as
well as TPS.

### Installation

First you will need to create Python files from the `.ui` files. Try this bit
of bash magic: 

```bash
for file in gui-ops/views/*ui; do pyuic5 "$file" -o "${file%.ui}.py"; done
```

Then you can run the main Python scripts. (All of this will probably be done by
`setup.py` at some point in the future.)

### Requirements

Developed in Python 3.7 and pyqt 5.6. Shouldn't require anything else to run,
although the resulting OPS file will require the branch for LAMMPS support.

### Tests

Tests are in development, and are planned to use:

* pytest
* pytest-qt
* pytest-bdd

After these are installed, the tests can be run with ???TODO???
