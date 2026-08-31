import secrets
import utils


class Transcript:

    def __init__(self):
        # Generate a random 32-byte value to initialize the transcript.
        self.sigma = secrets.token_bytes(32)

        # Store all recorded TSP search steps.
        self.steps = []

        # Index steps by their parent path and selected neighbour
        # so they can be found quickly during validation.
        self.path_index = {}

        # Create the hash of the initial transcript state.
        self.previous_hash = utils.create_hash(self.sigma)

    def add_step(self, data):
        # Assign the next sequential number to the step.
        step_number = len(self.steps) + 1

        # Include the previous hash, step number, and current data
        # to create a hash that links this step to the previous one.
        hash_data = self.previous_hash + str(step_number) + str(data)
        current_hash = utils.create_hash(hash_data)

        # Store the information about the current search step.
        self.steps.append({
            "step": step_number,
            "data": data,
            "previous_hash": self.previous_hash,
            "hash": current_hash
        })

        # Create a key using the parent path and selected neighbour
        # so the step can be retrieved directly during validation.
        key = (
            tuple(data["parent_path"]),
            data["selected_neighbour"]
        )

        self.path_index[key] = data

        # The current hash becomes the previous hash for the next step.
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
        # Create the data structure describing one TSP search step.
        return {
            # Path before selecting the next neighbour.
            "parent_path": parent_path[:],

            # Last vertex in the parent path.
            "parent_vertex": parent_vertex,

            # Lower bound of the parent node.
            "parent_lower_bound": parent_lower_bound,

            # Neighbour selected from the parent node.
            "selected_neighbour": selected_neighbour,

            # Path after adding the selected neighbour.
            "child_path": child_path[:],

            # Cost of the selected edge.
            "edge_cost": edge_cost,

            # Reduction applied when calculating the child lower bound.
            "reduction_cost": reduction_cost,

            # Lower bound of the child node.
            "child_lower_bound": child_lower_bound,

            # Indicates whether the child branch was pruned.
            "pruned": pruned
        }
