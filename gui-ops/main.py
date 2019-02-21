import sys
from PyQt5.QtWidgets import QApplication
import controllers

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # window = controllers.CVController()
    # window = controllers.StateController()
    window = controllers.SimController()
    window.show()
    sys.exit(app.exec_())
