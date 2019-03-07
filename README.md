# Qt-based GUI for some simple OpenPathSampling simulations

This includes some GUI tools for running some simple simulations with
OpenPathSampling. The overall approach is that one GUI app will help create
input files for OPS (initial trajectory, TPS, and committor simulations, all
with arbitrary number of states), and a second app will provide common
analysis tools. Many of those analysis tools will be relevant for TIS as
well as TPS.

### Installation

Install PyQt5. Due to some issues between pip and conda naming conventions, you
should do this before anything else.

Next you will need to create Python files from the `.ui` files. Try this bit
of bash magic: 

```bash
for file in gui-ops/views/*ui; do pyuic5 "$file" -o "${file%.ui}.py"; done
```

Then install using `pip install .` from the directory containing `setup.py`.
(Note: for now the scripts still need to be run by calling `python main.py`;
this will be changed at some point in the near future.)

### Requirements

Developed in Python 3.7 and pyqt 5.6. Shouldn't require anything else to run,
although the resulting OPS file will require the branch for LAMMPS support.


### Tests

Tests are in development, and are planned to use:

* pytest
* pytest-qt
* pytest-bdd

After these are installed, the tests can be run with ???TODO???
