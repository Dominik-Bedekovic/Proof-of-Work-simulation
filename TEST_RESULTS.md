# Verification results — 9 September 2026

Environment: Linux, Python 3.12.14. No native Windows GUI/display test was performed.

| Check | Outcome |
|---|---|
| `python proof_validation_tests.py` | 10/10 expected decisions; fixture now includes its required name |
| `python -m unittest -v test_regressions` | All 18 test methods passed |
| Exhaustive solver oracle within regressions | 600 complete symmetric integer instances, sizes 3–8, all optimal costs matched |
| Parallel scheduler + replay within regressions | 30 instances, sizes 5–7, heterogeneous worker rates; all optima matched enumeration and transcripts validated; nonminimum-bound completion order was exercised |
| Original five-city attack | 1870-cost path with claimed cost 1030 rejected |
| Seven-city attack | 2587-cost path with claimed cost 1813 rejected |
| Alternative optimum tour | Reversed symmetric optimum accepted |
| Invalid inputs | Invalid city types/indices/structure, nonfinite/nonnumeric costs and missing tour edges rejected |
| Dependency chain | Three one-second dependent tasks finish at 3 seconds |
| Final transcript work | One search second plus two append seconds finishes at 3 seconds |
| Outstanding append batches | Two children finishing at time 2 with five- and one-second ordered append batches drain at time 8 |
| PoW cutoff | 0.1-second success wins over 0.9-second success; exact floor counts, equal-time ties, cursors and nonce wrap checked |
| Complete solution payload | Original example reports closed optimal path and tour cost 1030 |
| Repeated integration | Two invocations per validation mode, two repetitions per algorithm per invocation; accounting components and reset state checked |
| Rejected proposals | Invalid result raises before averaging |
| Component calibration smoke | All six TSP/validation/append calibrators ran successfully |
| `spawn` integration | Both selected integration test methods passed, including 30 parallel proofs and repeated runs across modes |
| Normal calibration integration | Five workers, seven cities, difficulty 2, proof mode; default two-second-target benchmarks and full simulation passed |
| Compilation | All Python files compiled successfully |

The integration suite uses fixed synthetic rates to make accounting assertions reproducible. Benchmark smoke tests execute measured calibration, and `calibration_smoke.py` separately uses normal calibration. Controlled scheduler/PoW tests mock task results to create exact counterexamples; real scheduler, proof and council multiprocessing integration is also covered.

Normal-calibration example (random workload, not a recommended thesis result): 63 B&B nodes, 108 transcript records, search work 0.000869482 reference seconds, append work 0.000261795 reference seconds, validation work 0.001255326 reference seconds, total work 0.002386604 reference seconds. Simulated search-plus-append time was 0.864443 seconds and total time 2.584821 seconds. Values will differ on another run/machine.

Raw logs are in `test-results/`. `SOURCE_CHANGES.patch` compares revised source/document files with the reviewed upload. The entire updated project is included; no patch application is required.

These results address the six specified regressions within the documented educational model. Regenerate thesis experiments, update the algorithm/metric descriptions from `MODEL_NOTES.md`, and check the graphical interface on the submission machine. Spawn-mode success on Linux does not constitute native Windows/Python 3.13 GUI verification.
