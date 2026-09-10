# Corrected simulation model and thesis notes

This version addresses the six findings from the 9 September 2026 review. Rerun calibration and regenerate affected thesis figures; old numeric results are not comparable to the corrected scheduling/accounting.

## Validation

Proof and council validation share `_validate_proposed_tour`. It requires integer (not Boolean or float) city indices, a Hamiltonian cycle starting/ending at city 0, finite original edge costs, and a finite numeric claimed cost equal to the independently calculated edge sum.

Semantic replay also applies this guard, then reconstructs search states, reductions, incumbent changes, pruning and the exhausted frontier. The reconstructed optimum must equal the submitted cost. **Alternative tours with exactly the same optimum cost are allowed**; the submitted route need not be the same orientation as the transcript's winning route.

Parallel tasks may finish in a different order from their dispatch priority. Replay therefore permits any generated open node to complete, while preserving every structural, bound, pruning, incumbent and completeness check. It verifies the search certificate, not dispatch priority, worker identities, elapsed time or physically performed work. The old order test is now named `test_invalid_incumbent_history`: the specific shuffled records remain invalid because of incumbent-history inconsistencies. Other sound completion orders are intentionally accepted.

This remains full B&B semantic replay, not zero knowledge, a succinct proof, or proof that a miner freshly expended a particular amount of physical computation. Rehashing a known trace for the same TSP under a different sigma is still possible. The matrix/root is trusted input provided by the simulator. No adversarial network/consensus security claim is made.

## Causal search scheduling

`scheduler.run_search` models cooperative workers sharing a central ready queue and incumbent:

1. At time zero, only the root is ready. Idle workers reserve available minimum-bound tasks in worker-index order; workers without tasks stay idle.
2. One reserved B&B node takes `1 / worker.search_rate` simulated seconds. No search effect is applied at dispatch.
3. At search completion, the reserved node is processed using the then-current incumbent. Children and improved incumbents become visible at this timestamp. No other worker can process the reserved task.
4. Search-completion events at exactly equal timestamps are processed in worker-index order. All events already scheduled at that timestamp are processed before new dispatches. Floating-point event times are compared as stored; no arbitrary near-tie tolerance is applied.
5. In proof mode, logical transcript records are appended in search-completion order. Their modeled hash/append service is serialized in the same order, since each record needs the previous hash. A record batch starts at the later of search completion and the previous append batch's finish, and takes `records / worker.transcript_rate`. Its producing worker remains occupied while waiting and appending. Other workers may search using the already completed search effects.
6. A worker becomes idle after its logging service, or immediately at search completion if no logging is needed. There is no prepayment of search time while idle.
7. An empty ready queue is insufficient for termination: all reserved searches and queued/in-progress append service must finish. No dispatched work is canceled or credited fractionally. Validation starts only after this drain.

The simulator executes these state transitions sequentially in Python; event times model parallel resources, not wall-clock execution. Building the logical record immediately at search completion is a simulation bookkeeping action: modeled hash availability is represented by the serial append finish times. Workers cannot obtain their next task until their append finishes, and validation cannot read an unfinished certificate.

A three-task dependency chain with one-second tasks takes three seconds even with three workers. A final task with one second of search plus two seconds of append work takes three seconds. Two child tasks completing at time 2 with five seconds and one second of ordered append service finish logging at times 7 and 8 respectively.

The worker discovering the final best tour and the worker finishing the overall search/logging phase are reported separately. The former is used in the solution's `winner.name`; this is attribution in a cooperative model, not a consensus reward rule.

## Work units and boundaries

Every run retains separate counters and normalized components:

| Component | Raw field | Calibration |
|---|---|---|
| B&B search | `pouw_computations` | `computations_per_second` |
| Transcript record append | `transcript_records` | `transcript_per_second` |
| Hash-chain checking | `proof_hash_checks` | `hash_validation_per_second` |
| Semantic replay/setup | `proof_semantic_checks` | `semantic_validation_per_second` |
| Council tour validation | `council_initial_validations` | `initial_validations_per_second` |
| Council branch validation | `council_branch_validation_nodes` | `branch_validation_nodes_per_second` |

For the selected components, aggregate reference compute work is `sum(count / measured_rate)`. Waiting and parallel overlap change simulated elapsed time, not this aggregate work sum. `pouw_compute_work` includes search plus transcript append work; `total_compute_work` adds validation. `total_computations` is retained for compatibility but is **B&B-equivalent work**, not a raw heterogeneous operation count. Do not add it to the raw component counters.

The “Search + transcript generation” graph component is the proof-mode search phase, including append service and waiting. It is not a separately measured no-transcript baseline.

The model deliberately excludes TSP-instance setup, initial matrix reduction/root creation, construction of the root-children commitment and its initial hash, and mining record-dictionary construction from simulated mining work/time. The record benchmark measures `Transcript.add_step` on preconstructed dictionaries: serialization/hashing, list append and path indexing are the modeled transcript-generation component. Dictionary construction and initialization are therefore **not** claimed to be fully measured overhead. Semantic validation calibration includes its submitted-tour, root and replay checks; its units are a calibrated composite proxy.

Benchmark rates remain averages from a deterministic instance of the selected size. They do not make every B&B node or semantic record equally expensive in reality. State these limits and consider sensitivity/variance across representative matrices. Reference compute seconds are not measured energy in joules. Wall-clock timing also includes Python overhead, multiprocessing, printing, calibration and setup.

## PoW cutoff

Within the final one-second interval, select the success with minimum exact rational `hashes / hash_rate`; worker index breaks equal-time ties. For every worker, count `floor(rate * cutoff)` completed hashes. Each worker's next-attempt nonce/extra-nonce/Merkle state is advanced only to that cutoff, including wraparound. The winner payload separately retains the actual successful nonce.

Speculative hashes physically executed by the simulator beyond the modeled cutoff are not counted as simulated network work. This is distinct from runtime profiling.

## GUI solution fields

The displayed route is `Node.tsp.best_path`, including the final 0. The displayed tour cost is `Node.tsp.best_cost`, including the return edge. The search-node lower bound is explicitly labelled; the partial-path cost remains a separate diagnostic payload field. The end vertex is 0 and the visited-city count is the number of cities.

## Running and testing

Install dependencies and launch as before:

```sh
python -m pip install -r requirements.txt
python main.py
```

Run the supplied adversarial tests and new assertion-based regressions:

```sh
python proof_validation_tests.py
python -m unittest -v test_regressions
```

Optional spawn-mode integration (also works on Linux to exercise Windows-style process startup):

```sh
python test_regressions.py --spawn Regressions.test_repeat_modes_accounting_and_payload Regressions.test_parallel_transcripts_and_optima
```

Optional end-to-end run with normal two-second-target calibration:

```sh
python calibration_smoke.py
```

See the fresh logs in `test-results/` and execution instructions in `README.md`. These tests validate the stated simulation model and regressions; they are not a guarantee for arbitrary malformed certificate objects, sparse/disconnected graphs, every floating-point workload or a real distributed deployment. The supported experiment domain remains complete symmetric integer TSP matrices generated by the project. The thesis itself and native Windows GUI still need review on the submission machine.


## Host controls and paired inputs (10 September)

HostPool bounds actual processes independently of logical node/validator counts. A one-worker policy
executes directly; larger pools use spawn. PoW reuses its pool across batches. Hash workers receive only
their slices plus absolute index and preceding commitment. Cooperative cancellation checkpoints cover
calibration, solver, hashing and semantic replay; cancellation during a pool wait terminates its workers.
Worker exceptions propagate, and multi-process jobs time out rather than waiting forever after a lost worker.
Council remains unanimous over its disjoint branch checks.

The GUI benchmark repetition count is separate from simulation repetitions. The experiment runner freezes
all reference rates across modes and saves explicit matrices, rates, block inputs and sigma values.
Experiment sigma is reproducible test input; it is not an unpredictable security challenge. Workload input
pairing does not turn this educational model into a blockchain consensus protocol.
