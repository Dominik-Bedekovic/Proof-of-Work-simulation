"""Optional real-calibration integration smoke test (~10 seconds)."""
import json
from mainFunctions import MainFunctions
if __name__ == '__main__':
    MainFunctions.benchmarks_done=False
    simulation=MainFunctions(5,7,1,2,1)
    result=simulation.run_simulation()
    run=result['pouw']['runs'][0]
    assert run['validation_valid']
    assert run['winner']['path'][0]==run['winner']['path'][-1]==0
    assert run['transcript_records']>0
    assert run['transcript_compute_work']>0
    print('CALIBRATION SMOKE PASS')
    print(json.dumps({k:run[k] for k in ('pouw_computations','transcript_records','search_compute_work','transcript_compute_work','validation_compute_work','total_compute_work','pouw_time','total_time')},indent=2))
