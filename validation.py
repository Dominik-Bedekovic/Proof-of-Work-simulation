from tspData import TspData
from tspFunctions import TspFunction
import multiprocessing
import utils

def council_validation(tsp: TspData, council, proposed_path, proposed_cost):

    
    arguments = [(tsp, proposed_path, proposed_cost) for _ in council]

    with multiprocessing.Pool() as pool:

        results = pool.map(_validate_node, arguments)

    initial_votes = sum(results)
    
    total_votes = len(council)

    with multiprocessing.Pool() as pool:

        results = pool.map(_validate_branch, arguments)

    ultimate_votes = sum(results)

    print("Council votes: ")
    print(f"Initial votes: {initial_votes}")
    print(f"Ultimate votes: {ultimate_votes}")
    print(f"Total votes: {total_votes}")

    if (_council_voting(initial_votes, ultimate_votes, total_votes) is False):
        return False

    return True

def _validate_node(args):

    tsp, proposed_path, proposed_cost = args

    valid = True

    if proposed_path[0] != 0 or proposed_path[-1] != 0:
        valid = False

    elif len(proposed_path) != tsp.size + 1:
        valid = False

    elif len(set(proposed_path[:-1])) != tsp.size:
        valid = False

    else:

        total_cost = 0

        for i in range(len(proposed_path) - 1):

            source = proposed_path[i]
            destination = proposed_path[i + 1]

            edge_cost = tsp.matrix[source][destination]

            if edge_cost == utils.inf:
                valid = False
                break

            total_cost += edge_cost

        if total_cost != proposed_cost:
            valid = False

    return valid

def _validate_branch(args):

    tsp, branch, proposed_cost = args

    return TspFunction.validate_branch(
        tsp,
        branch,
        proposed_cost
    )

def _council_voting(initial_votes, ultimate_votes, total_votes):

    vote_ratio_initial = initial_votes / total_votes

    print(f"Initial vote ratio: {vote_ratio_initial}")

    vote_ratio_ultimate = ultimate_votes / total_votes

    print(f"Ultimate vote ratio: {vote_ratio_ultimate}")

    if (vote_ratio_initial < 0.5 or vote_ratio_ultimate < 0.5):
        return False

    return True
    