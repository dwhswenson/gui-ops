TPS_SETUP = """
network = paths.TPSNetwork(states)
scheme = paths.OneWayShootingMoveScheme(network, engine)

initial_conditions = scheme.initial_conditions_from_trajectories(trajectory)

sim = paths.PathSampling(
    storage=storage,
    move_scheme=scheme,
    sample_set=initial_conditions
)
"""


COMMITTOR_SETUP = """
sim = paths.CommittorSimulation(
    storage=storage,
    states=states,
    randomizer=randomizer,
    initial_snapshots=initial_conditions
"""

TRAJECTORY_SETUP = """
class TrajectorySimulation(paths.PathSimulator):
    def __init__(self, storage, states, engine, initial_conditions):
        self.storage = storage
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
"""

MAIN_RUN = """
if __name__ == "__main__":
    sim.run({n_sim_steps})
"""


