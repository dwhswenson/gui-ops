from functools import partial

from views import Ui_CVCreate, Ui_StateCreate, Ui_SimulationOverview
from code_writers import CVCodeWriter, VolumeCodeWriter
from PyQt5.QtWidgets import QDialog

class AddObjectDialog(object):
    """Extra methods for running another dialog to add objects to a dict

    Use by composition.
    """
    def __init__(self, controller, attribute, get_name, ui_elem,
                 modal=False):
        self.controller = controller
        self.attribute = attribute
        self.get_name = get_name
        self.ui_elem = ui_elem
        self.modal = modal

    def run_controller(self, **kwargs):
        ctrl = self.controller(**kwargs)  # TODO: add parent
        ctrl.setModal(self.modal)
        ctrl.show()
        ctrl.exec_()
        return ctrl

    def add(self):
        ctrl = self.run_controller()
        result = getattr(ctrl, self.attribute)
        name = self.get_name(result)
        self.ui_elem.addItem(name)
        return {name: result}

    # TODO: add edit method, which updates these


class CreateObjectDialog(object):
    """Mix-in for creating objects to be read by parent views

    Requires setting class variable ``CodeClass``, which is the
    ``CodeWriter`` model in this MVC group.

    Requires setting class variable ``target``, the name of the class
    attribute for the thing that will be created by this dialog.

    Requires implementing method ``_get_kwargs_from_ui()``, which gets the
    kwargs needed for the ``CodeWriter`` from the view.
    """
    def accept(self):
        kwargs = self._get_kwargs_from_ui()
        attr = getattr(self, self.target)
        if attr is None:
            setattr(self, self.target, self.__class__.CodeClass(**kwargs))
        else:
            attr.update(**kwargs)
        super(self.__class__, self).accept()


class QDialogController(QDialog):
    """Mix-in for generic QDialog controller stuff

    Requires setting class variable ``UIClass``, the view class for this MVC
    group.
    """
    def setup_ui(self):
        ui = self.__class__.UIClass()
        ui.setupUi(self)
        return ui


class CVController(QDialogController, CreateObjectDialog):
    comboBox_entries = {'LAMMPS Compute': "LAMMPSComputeCV"}
    target = "cv"
    CodeClass = CVCodeWriter
    UIClass = Ui_CVCreate

    def __init__(self, cv=None, engine=None):
        super(CVController, self).__init__()
        self.cv = cv
        self.engine = engine  # engine may be used in CV creation
        self.ui = self.setup_ui()

    def _get_kwargs_from_ui(self):
        cv_class = self.comboBox_entries[str(self.ui.cv_type.currentText())]
        return dict(name=self.ui.name.text(),
                    class_name=cv_class,
                    parameters=self.ui.parameters.text())


class StateController(QDialogController, CreateObjectDialog):
    target = "state"
    UIClass = Ui_StateCreate
    CodeClass = VolumeCodeWriter
    def __init__(self, state=None, cvs=None):
        super(StateController, self).__init__()
        self.state = state
        if cvs is None:
            cvs = {}
        self.cvs = cvs
        self.ui = self.setup_ui()

        self.add_cv_dialog = AddObjectDialog(
            controller=CVController,
            attribute="cv",
            get_name=lambda x: x.kwargs['name'],
            ui_elem=self.ui.collectivevariable,
            modal=True
        )

        # test each connections
        self.ui.is_periodic.stateChanged.connect(self.toggle_periodic_view)
        self.ui.addCV.clicked.connect(self.add_cv_action)

        # test each default behavior
        self._default_nonperiodic()

    def _get_kwargs_from_ui(self):
        periodic = 'Periodic' if self.ui.is_periodic else ''
        kwargs = dict(class_name=periodic + "CVDefinedVolume",
                      name=self.ui.name.text(),
                      lambda_min=self.ui.lambda_min.value(),
                      lambda_max=self.ui.lambda_max.value())
        if self.ui.is_periodic:
            kwargs.update(period_min=self.ui.period_min.value(),
                          period_max=self.ui.period_max.value())
        # TODO: tmp
        kwargs.update({'is_state': True})
        return kwargs

    def add_cv_action(self):
        result = self.add_cv_dialog.add()
        self.cvs.update(result)

    def _default_nonperiodic(self):
        self.ui.is_periodic.setCheckState(False)
        self.toggle_periodic_view()

    def toggle_periodic_view(self):
        self.ui.period_info.setEnabled(self.ui.is_periodic.isChecked())



class SimController(QDialog):
    def __init__(self, states=None, cvs=None, parent=None):
        super(SimController, self).__init__(parent)
        if cvs is None:
            cvs = {}
        if states is None:
            states = []

        self.cvs = cvs
        self.states = {}
        for state in states:
            self.add_state(state)

        self.ui = Ui_SimulationOverview()
        self.ui.setupUi(self)

        change_runtype = self.ui.run_type.currentTextChanged
        change_runtype.connect(self.update_sim_parameters)
        state_select = self.ui.state_list.itemSelectionChanged
        state_select.connect(self.toggle_buttons_state_sel)
        self.ui.add_state.clicked.connect(self.add_state_action)

        # defaults
        self.toggle_buttons_state_sel()
        self.update_sim_parameters()


    def toggle_buttons_state_sel(self):
        is_selected = bool(self.ui.state_list.selectedItems())
        self.ui.delete_state.setEnabled(is_selected)

    def update_sim_parameters(self):
        page = {
            "Transition trajectory": self.ui.traj_params,
            "Transition path sampling": self.ui.tps_params,
            "Committor simulation": self.ui.committor_params
        }[self.ui.run_type.currentText()]
        self.ui.sim_parameters.setCurrentWidget(page)

    def run_state_controller(self, state):
        state_ctrl = StateController(state=state, cvs=self.cvs)
        state_ctrl.setModal(True)
        state_ctrl.show()
        state_ctrl.exec_()
        return state_ctrl

    def add_state_action(self):
        state_ctrl = self.run_state_controller(state=None)
        self.add_state(state_ctrl.state)

    def add_state(self, state):
        self.states[state.name] = state
        self.ui.state_list.addItem(state.name)
