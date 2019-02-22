import sys
from PyQt5.QtWidgets import QApplication
import controllers
import argparse

# doing this with a variable here instead of argparse b/c I'm not sure that
# argparse will play nicely with Qt's argument parsing
GUI="main"
# GUI="alt"

def main_gui(self):
    cv_states = controllers.CVsAndStatesController()
    sim_details = controllers.SimDetailsController(
        cvs=cv_states.cvs,
        states=cv_states.states,
        previous=cv_states
    )
    cv_states.accepted.connect(sim_details.show)
    return cv_states

def alt_gui(self):
    window = controllers.SimController()
    return window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = {"main": main_gui,
           "alt": alt_gui}[GUI]
    window = gui()
    window.show()
    sys.exit(app.exec_())
