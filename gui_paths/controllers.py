from functools import partial

from .views import (Ui_CVCreate, Ui_StateCreate, Ui_SimulationOverview,
                   Ui_CVsAndStates, Ui_SimDetails)
from .code_writers import (
    CVCodeWriter, VolumeCodeWriter, StorageWriter, EngineWriter,
    StringWrapper, BlankLineCodeWriter, InitialTrajectoryWriter
)
from .output_run_py import RunPyFile
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
                 parent=None, modal=False, hidden_ui_elems=None):
        self.controller = controller
        self.attribute = attribute
        self.get_name = get_name
        self.ui_elem = ui_elem
        self.dct = dct
        self.parent = parent
        self.modal = modal
        if hidden_ui_elems is None:
            hidden_ui_elems = []
        self.hidden_ui_elems = hidden_ui_elems

    # TODO: abstract this to do different kinds; use a string input
    # 'modal_dialog', 'dialog', 'stack_page', ...
    def run_controller(self, **kwargs):
        ctrl = self.controller(parent=self.parent, **kwargs)
        ctrl.setModal(self.modal)
        ctrl.show()
        for elem in self.hidden_ui_elems:
            ui_elem = getattr(ctrl.ui, elem)
            ui_elem.setVisible(False)
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

        if self.parent:
            self.parent.update_after_add()
        return {name: result}

    def add_cv_name_to_ui(self, name):
        self.ui_elem.addItem(name)


class ObjectListWidgetController(AddObjectFromButton):
    """
    """
    def __init__(self, controller, attribute, get_name, ui_elem, dct,
                 parent=None, modal=False, hidden_ui_elems=None):
        super(ObjectListWidgetController, self).__init__(
            controller, attribute, get_name, ui_elem, dct, parent, modal,
            hidden_ui_elems
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

    def update_after_add(self):
        pass  # implement when needed in subclasses

    def input_errors(self):
        return False

    def toggle_enabled_ok(self):
        enabled = not bool(self.input_errors())
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)



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

        # TODO: :test each default behavior
        self._default_nonperiodic()
        self.toggle_enabled_ok()

        # TODO: test each connection
        self.ui.is_periodic.stateChanged.connect(self.toggle_periodic_view)
        ui = self.ui
        ui_signals = [ui.name.textChanged, ui.is_periodic.stateChanged,
                      ui.collectivevariable.currentTextChanged,
                      ui.lambda_min.textChanged, ui.lambda_max.textChanged,
                      ui.period_min.textChanged, ui.period_max.textChanged]
        for sig in ui_signals:
            sig.connect(self.toggle_enabled_ok)


    def _get_kwargs_from_ui(self):
        cv_name = self.ui.collectivevariable.currentText()
        is_periodic = self.ui.is_periodic.isChecked()

        try:
            cv_bound_name = self.cvs[cv_name].bound_name
        except KeyError:
            # not ready to return this yet! Ok should be disabled
            return {}

        try:
            lambda_min = float(self.ui.lambda_min.text())
            lambda_max = float(self.ui.lambda_max.text())
        except ValueError:
            return {}

        if is_periodic:
            try:
                period_min = float(self.ui.period_min.text())
                period_max = float(self.ui.period_max.text())
            except ValueError:
                return {}

        periodic = 'Periodic' if is_periodic else ''
        kwargs = dict(
            class_name=periodic + "CVDefinedVolume",
            collectivevariable=cv_bound_name,
            name=self.ui.name.text(),
            lambda_min=StringWrapper("float('{}')".format(lambda_min)),
            lambda_max=StringWrapper("float('{}')".format(lambda_max))
        )
        # explicit float calls above are sneaky trick to handle inf
        if is_periodic:
            kwargs.update(period_min=lambda_min,
                          period_max=lambda_max)
        # TODO: tmp
        kwargs.update({'is_state': True})
        return kwargs

    def toggle_periodic_view(self):
        self.ui.period_info.setEnabled(self.ui.is_periodic.isChecked())

    def toggle_enabled_ok(self):
        dct = self._get_kwargs_from_ui()
        if not dct:
            enabled = False
        else:
            is_named = bool(dct['name'])
            if dct['class_name'] == "CVDefinedVolume":
                # magic to strip this down to the relevant string
                l_min = float(str(dct['lambda_min'])[7:-2])
                l_max = float(str(dct['lambda_max'])[7:-2])
                acceptable_lambdas = (l_min < l_max)
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
        self.toggle_enabled_ok()

        change_runtype.connect(self.tmp_disable)
        self.tmp_disable()

    def update_after_add(self):
        self.toggle_enabled_ok()

    def toggle_enabled_ok(self):
        enabled = len(self.states) >= 2
        self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(enabled)

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
        self.ui.tps_init_traj.setText("trajectory.nc")
        self.ui.tps_init_traj.setEnabled(False)
        self.ui.tps_traj_idx.setEnabled(False)
        self.ui.tps_top_file.setEnabled(False)

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

class SimDetailsController(QDialogController):
    UIClass = Ui_SimDetails
    def __init__(self, states=None, cvs=None, previous=None):
        super(SimDetailsController, self).__init__()
        self.states = states
        if self.states is None:
            self.states = {}

        self.cvs = cvs
        if self.cvs is None:
            self.cvs = {}

        self.ui = self.setup_ui()

        change_runtype = self.ui.run_type.currentTextChanged
        change_runtype.connect(self.update_sim_parameters)

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
        self.ui.tps_init_traj.setText("trajectory.nc")
        self.ui.tps_init_traj.setEnabled(False)
        self.ui.tps_traj_idx.setEnabled(False)
        self.ui.tps_top_file.setEnabled(False)

    def update_sim_parameters(self):
        page = {
            "Transition trajectory": self.ui.traj_params,
            "Transition path sampling": self.ui.tps_params,
            "Committor simulation": self.ui.committor_params
        }[self.ui.run_type.currentText()]
        self.ui.sim_parameters.setCurrentWidget(page)

    def accept(self):
        run_type_text = self.ui.run_type.currentText()
        run_type = {
            "Transition trajectory": "trajectory",
            "Transition path sampling": "TPS",
            "Committor simulation": "committor"
        }[run_type_text]

        init_cond_writer = {
            "Transition trajectory": BlankLineCodeWriter(),
            "Transition path sampling": InitialTrajectoryWriter(
                trajectory_file=self.ui.tps_init_traj.text(),
                traj_num=self.ui.tps_traj_idx.value(),
                top_file=self.ui.tps_top_file.text()
            ),
            "Committor simulation": BlankLineCodeWriter()
        }[run_type_text]

        n_sim_steps = {
            "Transition trajectory": '',
            "Transition path sampling": int(self.ui.n_steps.text()),
            "Committor simulation": "TODO"
        }[run_type_text]
        # TODO: protect against stupid values in n_steps (like non-int)

        extra_info_dict = {
            'n_sim_steps': n_sim_steps
        }

        storage = StorageWriter(filename=self.ui.output_file.text(),
                                mode='w')
        engine = EngineWriter(self.ui.lammps_script.text())
        run_py = RunPyFile(run_type=run_type,
                           engine=engine,
                           cvs=list(self.cvs.values()),
                           volumes=list(self.states.values()),
                           other_writers=[storage, init_cond_writer],
                           extra_info_dict=extra_info_dict)
        with open("run.py", mode='w') as f:
            run_py.write(f)

        super(SimDetailsController, self).accept()


class CVsAndStatesController(QDialogController):
    UIClass = Ui_CVsAndStates
    def __init__(self, states=None, cvs=None, parent=None):
        super(CVsAndStatesController, self).__init__(parent)
        self.states = states
        if self.states is None:
            self.states = {}

        self.cvs = cvs
        if self.cvs is None:
            self.cvs = {}

        self.ui = self.setup_ui()

        self.cv_list_controller = ObjectListWidgetController(
            controller=CVController,
            attribute='cv',
            get_name=lambda x: x.kwargs['name'],
            ui_elem=self.ui.cv_list,
            dct=self.cvs,
            parent=self,
            modal=True
        )
        self.cv_list_controller.make_connections(
            add_button=self.ui.add_cv,
            delete_button=self.ui.delete_cv
        )

        self.state_list_controller = ObjectListWidgetController(
            controller=StateController,
            attribute='state',
            get_name=lambda x: x.name,
            ui_elem=self.ui.state_list,
            dct=self.states,
            parent=self,
            modal=True,
            hidden_ui_elems=['addCV']
        )
        self.state_list_controller.make_connections(
            add_button=self.ui.add_state,
            delete_button=self.ui.delete_state
        )

        cancel = self.ui.buttonBox.button(QDialogButtonBox.Cancel)
        cancel.setDefault(False)
        cancel.setAutoDefault(False)
        self.toggle_enabled_ok()
        self.toggle_add_state()
        cancel.clearFocus()

    def toggle_add_state(self):
        enabled = len(self.cvs) > 0
        self.ui.add_state.setEnabled(enabled)

    def update_after_add(self):
        self.toggle_enabled_ok()
        self.toggle_add_state()

    def toggle_enabled_ok(self):
        enabled = len(self.states) >= 2
        ok_button = self.ui.buttonBox.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(enabled)
        if enabled:
            ok_button.setDefault(True)

