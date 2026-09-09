import utils


class Transcript:
    """
    Stores the Proof Validation transcript produced during the TSP
    Branch and Bound search.

    The transcript forms a hash chain:

        root_hash
            ↓
        step 1 hash
            ↓
        step 2 hash
            ↓
        step 3 hash
            ...

    Every step contains:
    - the logical search event,
    - the previous step hash,
    - the current step hash.

    This allows the validator to detect transcript modification,
    removal, or reordering because changing one record changes all
    following hashes.

    The transcript does not by itself prove when the computation was
    performed. Semantic validation later checks whether the recorded
    B&B operations are actually correct.
    """

    def __init__(
        self,
        root_data,
        root_hash
    ):
        """
        Initialize a new transcript.

        Parameters
        ----------
        root_data:
            Information describing the initial B&B root state.

        root_hash:
            Hash that binds the transcript root to the TSP instance
            and the challenge value used by the simulation.
        """

        # Step 0 is the transcript root.
        #
        # Unlike later records, it does not have a previous hash because
        # it represents the beginning of the hash chain.
        self.root = {
            "step": 0,
            "data": root_data,
            "previous_hash": None,
            "hash": root_hash
        }

        # Store every search event generated after the root.
        #
        # Examples include:
        # - branch creation,
        # - pruning,
        # - completed tours,
        # - dead ends.
        self.steps = []

        # Store selected transcript records in a lookup table.
        #
        # The key is:
        #
        #     (parent_path, selected_neighbour)
        #
        # This makes it possible to locate a recorded branch or complete
        # transition directly instead of scanning the entire transcript.
        self.path_index = {}

        # The first generated transcript step must reference the root hash.
        #
        # After every call to add_step(), this is updated to the new
        # current hash.
        self.previous_hash = root_hash

    def add_step(
        self,
        data
    ):
        """
        Add one search event to the transcript and extend the hash chain.

        The new record hash depends on:
        - the previous transcript hash,
        - the new step number,
        - the event data.

        Therefore, modifying or reordering an earlier step changes the
        expected hashes of every later step.
        """

        # Transcript steps begin at 1 because the root is step 0.
        step_number = (
            len(self.steps)
            + 1
        )

        # Bind this record to the previous transcript state.
        #
        # Including the step number also prevents the same data record
        # from being moved to another position without changing its hash.
        hash_data = (
            self.previous_hash
            + str(step_number)
            + str(data)
        )

        # Calculate the hash for this transcript record.
        current_hash = (
            utils.create_hash(
                hash_data
            )
        )

        # Store both hashes with the event.
        #
        # previous_hash links this record backward.
        # hash identifies the state of the transcript after this record.
        self.steps.append({
            "step":
                step_number,

            "data":
                data,

            "previous_hash":
                self.previous_hash,

            "hash":
                current_hash
        })

        # Branch and complete-tour records represent transitions from
        # a parent path to a selected next city.
        #
        # Indexing them lets validation retrieve the relevant event by
        # its logical search transition.
        if (
            data.get("type")
            in (
                "branch",
                "complete"
            )
        ):

            key = (
                tuple(
                    data[
                        "parent_path"
                    ]
                ),
                data[
                    "selected_neighbour"
                ]
            )

            self.path_index[
                key
            ] = data

        # The next transcript record must link to the hash of this record.
        self.previous_hash = (
            current_hash
        )

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
        """
        Create a transcript record for a generated B&B child.

        This record contains enough information for semantic validation
        to independently reconstruct the child and verify:

        - the parent node,
        - selected destination,
        - original edge cost,
        - matrix-reduction cost,
        - resulting child lower bound,
        - incumbent value at generation time,
        - whether pruning was justified.

        A branch record is created even when the child is immediately
        pruned. This is important because every legal branch must still
        be accounted for in the proof.
        """

        return {
            # Record type used by semantic replay.
            "type":
                "branch",

            # Partial route from which the child was generated.
            "parent_path":
                parent_path[:],

            # Current city of the parent node.
            "parent_vertex":
                parent_vertex,

            # Branch and Bound lower bound of the parent.
            "parent_lower_bound":
                parent_lower_bound,

            # City selected as the next destination.
            "selected_neighbour":
                selected_neighbour,

            # Resulting partial route after adding the destination.
            "child_path":
                child_path[:],

            # Actual TSP edge cost from the original distance matrix.
            "edge_cost":
                edge_cost,

            # Additional lower-bound contribution produced by reducing
            # the child's modified cost matrix.
            "reduction_cost":
                reduction_cost,

            # Full B&B lower bound calculated for the child.
            "child_lower_bound":
                child_lower_bound,

            # Best complete-tour cost known when this child was created.
            #
            # This is required because pruning must be justified using
            # the incumbent that existed at that exact point in the
            # recorded computation.
            "incumbent_cost":
                incumbent_cost,

            # True when the child was not inserted into the search queue
            # because its lower bound could not improve the incumbent.
            "pruned":
                pruned
        }

    @staticmethod
    def create_prune_data(
        path,
        vertex,
        lower_bound,
        incumbent_cost
    ):
        """
        Create a transcript record for pop-time pruning.

        A node may have been inserted into the priority queue while the
        incumbent was still weak. Before that node is eventually processed,
        another worker or branch may discover a better complete tour.

        Therefore, when the node is popped later, its lower bound may now
        be greater than or equal to the current incumbent and the complete
        subtree can be safely discarded.
        """

        return {
            # Distinguishes this event from branch generation.
            "type":
                "prune",

            # Path represented by the pruned node.
            "path":
                path[:],

            # Current city of the node.
            "vertex":
                vertex,

            # Lower bound used to determine whether the subtree can
            # still improve the best known solution.
            "lower_bound":
                lower_bound,

            # Best known complete-tour cost when pruning occurred.
            "incumbent_cost":
                incumbent_cost
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
        """
        Create a transcript record when a full Hamiltonian tour is closed.

        At this point every city has already been visited exactly once.
        The only remaining operation is adding the edge from the final
        city back to city 0.

        The incumbent stored here is the incumbent BEFORE the completed
        tour is allowed to improve it. This preserves the correct search
        chronology for semantic replay.
        """

        return {
            # Marks this record as a completed-tour event.
            "type":
                "complete",

            # Partial path before returning to city 0.
            "parent_path":
                parent_path[:],

            # Last city visited before closing the cycle.
            "parent_vertex":
                parent_vertex,

            # Lower bound associated with the final B&B search node.
            "parent_lower_bound":
                parent_lower_bound,

            # Closing a tour always selects city 0.
            "selected_neighbour":
                0,

            # Fully closed Hamiltonian cycle.
            "child_path":
                child_path[:],

            # Actual edge cost for returning to the starting city.
            "edge_cost":
                edge_cost,

            # No new reduced child node is constructed when closing
            # the tour, so these values do not apply.
            "reduction_cost":
                None,

            "child_lower_bound":
                None,

            # Incumbent before the complete tour is evaluated.
            "incumbent_cost":
                incumbent_cost,

            # A completed tour is evaluated rather than treated as a
            # generated/pruned child.
            "pruned":
                False
        }

    @staticmethod
    def create_dead_end_data(
        path,
        vertex,
        lower_bound,
        incumbent_cost,
        reason
    ):
        """
        Create a transcript record for a search node that cannot continue.

        A dead end represents a B&B node that is structurally legitimate
        but cannot lead to another useful search state.

        For example, after all cities have been visited there may be no
        finite edge from the final city back to city 0.

        Recording dead ends is important because semantic validation must
        be able to account for every processed branch rather than silently
        losing part of the search space.
        """

        return {
            # Identifies this as a terminal non-solution search state.
            "type":
                "dead_end",

            # Partial route represented by the node.
            "path":
                path[:],

            # Current city at the end of the partial route.
            "vertex":
                vertex,

            # B&B lower bound of the dead-end node.
            "lower_bound":
                lower_bound,

            # Best known complete solution when the node was processed.
            "incumbent_cost":
                incumbent_cost,

            # Human-readable / machine-readable explanation for why the
            # branch could not continue, for example:
            #
            #     "no_return_edge"
            #
            "reason":
                reason
        }
