import utils


class Transcript:

    def __init__(self, root_data, root_hash):

        self.root = {
            "step": 0,
            "data": root_data,
            "previous_hash": None,
            "hash": root_hash
        }

        # Store all recorded TSP search steps.
        self.steps = []

        # Index steps by their parent path and selected neighbour
        # so they can be found quickly during validation.
        self.path_index = {}

        self.previous_hash = root_hash

    def add_step(self, data):

        step_number = len(self.steps) + 1

        hash_data = (
            self.previous_hash
            + str(step_number)
            + str(data)
        )

        current_hash = utils.create_hash(
            hash_data
        )

        self.steps.append({
            "step": step_number,
            "data": data,
            "previous_hash": self.previous_hash,
            "hash": current_hash
        })

        if data.get("type") in ("branch", "complete"):

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
        incumbent_cost,
        pruned
    ):

        return {
            "type": "branch",
            "parent_path": parent_path[:],
            "parent_vertex": parent_vertex,
            "parent_lower_bound": parent_lower_bound,
            "selected_neighbour": selected_neighbour,
            "child_path": child_path[:],
            "edge_cost": edge_cost,
            "reduction_cost": reduction_cost,
            "child_lower_bound": child_lower_bound,
            "incumbent_cost": incumbent_cost,
            "pruned": pruned
        }


    @staticmethod
    def create_prune_data(
        path,
        vertex,
        lower_bound,
        incumbent_cost
    ):

        return {
            "type": "prune",
            "path": path[:],
            "vertex": vertex,
            "lower_bound": lower_bound,
            "incumbent_cost": incumbent_cost
        }


    @staticmethod
    def create_complete_data(
        parent_path,
        parent_vertex,
        parent_lower_bound,
        child_path,
        edge_cost,
        incumbent_cost
    ):

        return {
            "type": "complete",
            "parent_path": parent_path[:],
            "parent_vertex": parent_vertex,
            "parent_lower_bound": parent_lower_bound,
            "selected_neighbour": 0,
            "child_path": child_path[:],
            "edge_cost": edge_cost,
            "reduction_cost": None,
            "child_lower_bound": None,
            "incumbent_cost": incumbent_cost,
            "pruned": False
        }