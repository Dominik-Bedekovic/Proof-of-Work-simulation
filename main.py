"""Start the desktop application with multiprocessing support."""

from multiprocessing import freeze_support
if __name__ == "__main__":
    freeze_support()
    import argparse
    parser = argparse.ArgumentParser(description="PoW/PoUW simulator")
    parser.add_argument("--host-workers", type=int, default=1)
    parser.add_argument("--cpu-percent", type=int, help="Optional Windows job-wide CPU cap")
    options = parser.parse_args()
    if options.host_workers < 1:
        parser.error("--host-workers must be positive")
    if options.cpu_percent is not None:
        from windowsCpuLimit import apply_cpu_limit
        apply_cpu_limit(options.cpu_percent)
    # Spawned workers import this entry module without importing the GUI stack.
    import gui
    gui.start_gui(default_host_workers=options.host_workers)
