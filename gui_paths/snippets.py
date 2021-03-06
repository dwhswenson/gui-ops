TPS_SETUP = """
if len(states) > 2:
    initial_states = states
    final_states = states
else:
    initial_states, final_states = states

network = paths.TPSNetwork(initial_states, final_states)
scheme = paths.OneWayShootingMoveScheme(network, engine)

initial_conditions = scheme.initial_conditions_from_trajectories(trajectory)

sim = paths.PathSampling(
    storage=storage,
    move_scheme=scheme,
    sample_set=initial_conditions
)
"""[1:-1]


COMMITTOR_SETUP = """
sim = paths.CommittorSimulation(
    storage=storage,
    states=states,
    randomizer=randomizer,
    initial_snapshots=initial_conditions)
"""

TRAJECTORY_SETUP = """
class TrajectorySimulation(paths.PathSimulator):
    def __init__(self, storage, states, engine, initial_conditions=None):
        self.storage = storage
        if initial_conditions is None:
            initial_conditions = engine.current_snapshot
        self.initial_conditions = initial_conditions
        self.states = states
        self.engine = engine
        all_volumes = paths.join_volumes([s for s in self.states])
        self.ensemble = paths.SequentialEnsemble([
            paths.join_ensembles([paths.AllOutXEnsemble(state)
                                  for state in self.states]),
            paths.LengthEnsemble(1) & paths.AllInXEnsemble(all_volumes)
        ])

    def run(self):
        traj = self.engine.generate(self.initial_conditions,
                                    running=[self.ensemble.can_append])
        if self.storage:
            self.storage.save(traj)
            self.storage.save(self.initial_conditions)
            self.storage.save(self.engine)
            self.storage.save(self.states)
            self.storage.save(self.ensemble)
            self.storage.sync_all()

sim = TrajectorySimulation(storage, states, engine)
"""

MAIN_RUN = """
if __name__ == "__main__":
    sim.run({n_sim_steps})
"""

OPS_LOAD_TRAJ = """
inp_traj_file = paths.Storage("{traj_file}", mode='r')
trajectory = inp_traj_file.trajectories[{traj_num}]
"""[1:-1]
