import secrets
import utils


class Transcript:

    def __init__(self):
        self.sigma = secrets.token_bytes(32)
        self.steps = []
        self.step_index = {}
        self.path_index = {}
        self.previous_hash = utils.create_hash(self.sigma)

    def add_step(self, data):
        hash_data = self.previous_hash + str(data)
        current_hash = utils.create_hash(hash_data)

        self.steps.append({
            "data": data,
            "previous_hash": self.previous_hash,
            "hash": current_hash
        })

        # One transcript step corresponds to one computation.
        self.step_index[data["computation"]] = data

        key = (
        tuple(data["parent_path"]),
        data["selected_neighbour"]
    )

        self.path_index[key] = data

        self.previous_hash = current_hash

    def verify(self):

        previous_hash = utils.create_hash(self.sigma)

        for index, step in enumerate(self.steps):

            if step["previous_hash"] != previous_hash:
                print(
                    f"[VERIFY] Step {index}: "
                    f"previous hash mismatch"
                )
                return False

            hash_data = (
                previous_hash
                + str(step["data"])
            )

            expected_hash = utils.create_hash(
                hash_data
            )

            if step["hash"] != expected_hash:
                print(
                    f"[VERIFY] Step {index}: "
                    f"hash mismatch"
                )
                return False

            previous_hash = step["hash"]

        print(
            f"[VERIFY] Transcript valid "
            f"({len(self.steps)} steps)"
        )

        return True

    @staticmethod
    def create_step_data(
    computation,
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
            "computation": computation,

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