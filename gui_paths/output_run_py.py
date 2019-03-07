from snippets import TPS_SETUP, COMMITTOR_SETUP, TRAJECTORY_SETUP, MAIN_RUN

class RunPyFile(object):
    def __init__(self, run_type, cvs, volumes, engine, other_writers=None,
                 extra_info_dict=None):
        self.run_type = run_type
        self.cvs = cvs
        self.engine = engine
        self.volumes = volumes
        self.other_writers = other_writers
        self.extra_info_dict = extra_info_dict

    @property
    def code(self):
        sim_setup = {
            'TPS': TPS_SETUP,
            'committor': COMMITTOR_SETUP,
            'trajectory': TRAJECTORY_SETUP
        }[self.run_type]
        run_py = "import openpathsampling as paths\n"
        run_py += "import openpathsampling.engines.lammps as ops_lammps\n"
        for writer in [self.engine] + self.cvs + self.volumes:
            run_py += writer.code + "\n"

        states = [writer for writer in self.volumes if writer.is_state]
        states_str = "[" + ", ".join(s.bound_name for s in states) + "]"
        run_py += "states = {states}\n".format(states=states_str)

        for writer in self.other_writers:
            run_py += writer.code + "\n"

        # TODO: get initial conditions
        # TODO: get randomizer for committor (just take it from temperature)
        # TODO: get storage file
        # TODO: get engine
        # TODO: get n_sim_steps
        n_sim_steps = ""

        run_py += sim_setup.format(**self.extra_info_dict)
        run_py += MAIN_RUN.format(**self.extra_info_dict)

        return run_py

    def write(self, stream):
        stream.write(self.code)
