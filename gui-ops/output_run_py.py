from snippets import TPS_SETUP, COMMITTOR_SETUP, TRAJECTORY_SETUP, MAIN_RUN

class RunPyFile(object):
    def __init__(self, run_type, cv_writers, volume_writers,
                 other_writers=None):
        self.run_type = run_type
        self.cv_writers = cv_writers
        self.volume_writers = volume_writers
        self.other_writers = other_writers

    @property
    def code(self):
        sim_setup = {
            'TPS': TPS_SETUP,
            'committor': COMMITTOR_SETUP,
            'trajectory': TRAJECTORY_SETUP
        }[self.run_type]
        run_py = "import openpathsampling as paths\n"
        for writer in self.cv_writers + self.volume_writers:
            run_py += writer.code + "\n"

        state_writers = [writer for writer in self.volume_writers
                         if writer.is_state]
        states_str = "[" + ", ".join(s.bound_name for s in states) + "]"
        run_py += "states = {states}".format(states=states_str)

        # TODO: get initial conditions
        # TODO: get randomizer for committor (just take it from temperature)
        # TODO: get storage file
        # TODO: get engine
        # TODO: get n_sim_steps
        run_py += sim_setup
        run_py += MAIN_RUN.format(n_sim_steps=n_sim_steps)

        return run_py

    def write(self, stream):
        stream.write(self.code)
