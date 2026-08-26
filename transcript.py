import secrets
import utils


class Transcript:

    def __init__(self):
        self.sigma = secrets.token_bytes(32)
        self.steps = []
        self.path_index = {}
        self.previous_hash = utils.create_hash(self.sigma)

    def add_step(self, data):

        step_number = len(self.steps) + 1

        hash_data = self.previous_hash + str(step_number) + str(data)
        current_hash = utils.create_hash(hash_data)

        self.steps.append({
            "step": step_number,
            "data": data,
            "previous_hash": self.previous_hash,
            "hash": current_hash
        })

        key = (
        tuple(data["parent_path"]),
        data["selected_neighbour"]
    )

        self.path_index[key] = data

        self.previous_hash = current_hash

    @staticmethod
    def create_step_data(
    parent_path,
    parent_vertex,
    parent_lower_bound,
    selected_neighbour,
    child_path,
    edge_cost,
    reduction_cost,
    child_lower_bound,
    pruned
    ):
        return {
            "parent_path": parent_path[:],
            "parent_vertex": parent_vertex,
            "parent_lower_bound": parent_lower_bound,

            "selected_neighbour": selected_neighbour,
            "child_path": child_path[:],

            "edge_cost": edge_cost,
            "reduction_cost": reduction_cost,
            "child_lower_bound": child_lower_bound,

            "pruned": pruned
        }