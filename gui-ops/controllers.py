from functools import partial

from views import Ui_CVCreate, Ui_StateCreate, Ui_SimulationOverview
from code_writers import (
    CVCodeWriter, VolumeCodeWriter, StorageWriter, EngineWriter
)
from output_run_py import RunPyFile
from PyQt5.QtWidgets import QDialog, QDialogButtonBox

from PyQt5.QtWidgets import QListWidget, QComboBox

class AddObjectFromButton(object):
    """Extra methods for running another dialog to add objects to a dict

    Use by composition.

    Parameters
    ----------
    controller :
        the dialog to open in order to create the desired object
    attribute : str
        name of the attribute that the object is bound to in the controller
    get_name : callable
        method for obtaining the object's name from the object
    ui_elem :
        the UI element in the current view where the object will be listed;
        must support ``.addItem`` (``QListWidget``, ``QComboBox``, ...)
    dct : dict
        the dictionary storing the result object for parent controllers
        (using names as keys)
    parent : 
        parent view/controller for the new controller
    modal : bool
        whether the dialog should be modal
    """
    def __init__(self, controller, attribute, get_name, ui_elem, dct,
                 parent=None, modal=False):
        self.controller = controller
        self.attribute = attribute
        self.get_name = get_name
        self.ui_elem = ui_elem
        self.dct = dct
        self.parent = parent
        self.modal = modal

    # TODO: abstract this to do different kinds; use a string input
    # 'modal_dialog', 'dialog', 'stack_page', ...
    def run_controller(self, **kwargs):
        ctrl = self.controller(parent=self.parent, **kwargs)
        ctrl.setModal(self.modal)
        ctrl.show()
        ctrl.exec_()
        return ctrl

    def make_connections(self, add_button):
        add_button.clicked.connect(self.add)

    def add(self):
        ctrl = self.run_controller()
        result = getattr(ctrl, self.attribute)
        name = None
        if result:
            name = self.get_name(result)
            self.add_cv_name_to_ui(name)
            self.dct[name] = result
        return {name: result}

    def add_cv_name_to_ui(self, name):
        self.ui_elem.addItem(name)


class ObjectListWidgetController(AddObjectFromButton):
    """
    """
    def __init__(self, controller, attribute, get_name, ui_elem, dct,
                 parent=None, modal=False):
        super(ObjectListWidgetController, self).__init__(
            controller, attribute, get_name, ui_elem, dct, parent, modal
        )
        self.delete_button = None

    def make_connections(self, add_button, delete_button=None):
        super(ObjectListWidgetController, self).make_connections(add_button)
        # TODO: add double-click to edit
        if delete_button:
            self.delete_button = delete_button
            self.delete_button.clicked.connect(self.delete)

        self.ui_elem.itemSelectionChanged.connect(self.toggle_buttons)

        # set defaults
        self.toggle_buttons()

    def toggle_buttons(self):
        if self.delete_button:
            self.delete_button.setEnabled(bool(self.ui_elem.selectedItems()))

    def delete(self):
        pass

    def edit(self):
        pass



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

    def __init__(self, cv=None, engine=None, parent=None):
        super(CVController, self).__init__(parent=parent)
        self.cv = cv
        self.engine = engine  # engine may be used in CV creation
        self.ui = self.setup_ui()

        self.ui.name.textChanged.connect(self.toggle_enabled_ok)
        self.ui.parameters.textChanged.connect(self.toggle_enabled_ok)

        # defaults
        self.toggle_enabled_ok()

    def _get_kwargs_from_ui(self):
        cv_class = self.comboBox_entries[str(self.ui.cv_type.currentText())]
        extract_style = int(self.ui.extract_style.currentText()[0])
        extract_type = int(self.ui.extract_type.currentText()[0])
        return dict(name=self.ui.name.text(),
                    extract_style=extract_style,
                    extract_type=extract_type,
                    engine="engine",
                    class_name=cv_class,
                    groupid_style_args=self.ui.parameters.text())

    def toggle_enabled_ok(self):
        name = self.ui.name.text()
        params = self.ui.parameters.text()
        is_filled = bool(name) and bool(params)
        parent = self.parent()
        name_not_taken = name not in parent.cvs if parent else True
        enabled = is_filled and name_not_taken
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)


class StateController(QDialogController, CreateObjectDialog):
    target = "state"
    UIClass = Ui_StateCreate
    CodeClass = VolumeCodeWriter
    def __init__(self, state=None, parent=None):
        super(StateController, self).__init__(parent=parent)
        self.state = state
        self.ui = self.setup_ui()

        if parent:
            self.cvs = parent.cvs
        else:
            self.cvs = {}

        self.add_cv_dialog = AddObjectFromButton(
            controller=CVController,
            attribute="cv",
            dct=self.cvs,
            get_name=lambda x: x.kwargs['name'],
            ui_elem=self.ui.collectivevariable,
            modal=True
        )
        self.add_cv_dialog.make_connections(self.ui.addCV)

        # TODO: move this into the AddObjectFromButton
        for cv_name in self.cvs:
            self.add_cv_dialog.add_cv_name_to_ui(cv_name)

        # TODO: test each connection
        self.ui.is_periodic.stateChanged.connect(self.toggle_periodic_view)

        # TODO: :test each default behavior
        self._default_nonperiodic()

    def _get_kwargs_from_ui(self):
        cv_name = self.ui.collectivevariable.currentText()
        periodic = 'Periodic' if self.ui.is_periodic.isChecked() else ''
        kwargs = dict(class_name=periodic + "CVDefinedVolume",
                      collectivevariable=self.cvs[cv_name].bound_name,
                      name=self.ui.name.text(),
                      lambda_min=float(self.ui.lambda_min.text()),
                      lambda_max=float(self.ui.lambda_max.text()))
        if self.ui.is_periodic.isChecked():
            kwargs.update(period_min=float(self.ui.period_min.text()),
                          period_max=float(self.ui.period_max.text()))
        # TODO: tmp
        kwargs.update({'is_state': True})
        return kwargs

    def toggle_periodic_view(self):
        self.ui.period_info.setEnabled(self.ui.is_periodic.isChecked())

    def toggle_enabled_ok(self):
        dct = self._get_kwargs_from_ui(self)
        is_named = bool(dct['name'])
        if dct['class_name'] == "CVDefinedVolume":
            acceptable_lambdas = (dct['lambda_min'] < dct['lambda_max'])
        elif dct['class_name'] == "PeriodicCVDefinedVolume":
            acceptable_lambdas = (dct['period_min'] < dct['period_max'])

        enabled = is_named and acceptable_lambdas
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)

    def _default_nonperiodic(self):
        self.ui.is_periodic.setCheckState(False)
        self.toggle_periodic_view()


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

        self.state_list_controller = ObjectListWidgetController(
            controller=StateController,
            attribute='state',
            get_name=lambda x: x.name,
            ui_elem=self.ui.state_list,
            dct=self.states,
            parent=self,
            modal=True
        )
        self.state_list_controller.make_connections(
            add_button=self.ui.add_state,
            delete_button=self.ui.delete_state
        )

        # defaults
        self.update_sim_parameters()

        change_runtype.connect(self.tmp_disable)
        self.tmp_disable()

    def tmp_disable(self):
        self.ui.lammps_script.setText("script.lammps")
        self.ui.lammps_script.setEnabled(False)
        output_name = {
            'Transition trajectory': 'trajectory.nc',
            'Transition path sampling': 'tps.nc',
            'Committor simulation': 'committor.nc'
        }[self.ui.run_type.currentText()]
        self.ui.output_file.setText(output_name)
        self.ui.output_file.setEnabled(False)
        self.ui.traj_init_traj.setEnabled(False)
        self.ui.traj_init_frame.setEnabled(False)
        self.ui.tps_init_traj.setEnabled(False)

    def update_sim_parameters(self):
        page = {
            "Transition trajectory": self.ui.traj_params,
            "Transition path sampling": self.ui.tps_params,
            "Committor simulation": self.ui.committor_params
        }[self.ui.run_type.currentText()]
        self.ui.sim_parameters.setCurrentWidget(page)

    def accept(self):
        run_type = {
            "Transition trajectory": "trajectory",
            "Transition path sampling": "TPS",
            "Committor simulation": "committor"
        }[self.ui.run_type.currentText()]
        storage = StorageWriter(filename=self.ui.output_file.text(),
                                mode='w')
        engine = EngineWriter(self.ui.lammps_script.text())
        run_py = RunPyFile(run_type=run_type,
                           engine=engine,
                           cvs=list(self.cvs.values()),
                           volumes=list(self.states.values()),
                           other_writers=[storage])
        with open("run.py", mode='w') as f:
            run_py.write(f)

        super(SimController, self).accept()

