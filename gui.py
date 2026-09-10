"""Tkinter interface for configuring experiments and displaying work and time results."""

import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mainFunctions import MainFunctions
import time
import threading
from hostRuntime import cancellation, SimulationCancelled

host_workers = None
benchmark_runs = None
experiment_seed = None
cancel_event = threading.Event()
active_thread = None
closing = False


def close_application():
    """Cancel active work and let its pool cleanup finish before destroying Tk."""
    global closing
    closing = True
    cancel_event.set()
    root.withdraw()

    def finish_close():
        if active_thread is not None and active_thread.is_alive():
            root.after(50, finish_close)
        else:
            root.destroy()

    finish_close()

NO_VALIDATION = 0
PROOF_VALIDATION = 1
COUNCIL_VALIDATION = 2
root = None
settings_frame = None
loading_frame = None
results_container = None
results_canvas = None
results_frame = None
comparison_frame = None
node_frame = None
nodes = None
runs = None
difficulty = None
cities = None
validation = None
configuration_nodes_label = None
configuration_runs_label = None
configuration_difficulty_label = None
configuration_cities_label = None
pow_hash_rate_label = None
pow_average_hashes_label = None
pouw_computation_rate_label = None
pouw_average_computations_label = None
average_hashes_label = None
average_computations_label = None
pow_simulation_time_label = None
pouw_simulation_time_label = None
run_button = None
progress_bar = None
progress_label = None
normal_geometry = None
pow_compute_work_label = None
pouw_compute_work_label = None


def run_settings():
    """Read GUI settings on the Tkinter thread and start the background experiment."""

    global active_thread
    # Read Tkinter values before launching the worker thread.
    selected_nodes = nodes.get()
    selected_cities = cities.get()
    selected_runs = runs.get()
    selected_difficulty = difficulty.get()
    selected_validation = validation.get()
    try:
        selected_host_workers = int(host_workers.get())
        selected_benchmark_runs = int(benchmark_runs.get())
        selected_seed = int(experiment_seed.get())
        if selected_host_workers < 1 or selected_benchmark_runs < 1:
            raise ValueError()
    except (ValueError, tk.TclError):
        messagebox.showerror("Invalid settings", "Workers and benchmark repetitions must be positive integers; seed must be an integer.")
        return
    cancel_event.clear()
    if selected_validation == "none":
        validation_mode = NO_VALIDATION
    elif selected_validation == "proof":
        validation_mode = PROOF_VALIDATION
    elif selected_validation == "council":
        validation_mode = COUNCIL_VALIDATION
    else:
        validation_mode = NO_VALIDATION
    progress_bar["value"] = 0
    progress_label.config(text="Starting simulation... 0 / 100")
    settings_frame.grid_remove()
    loading_frame.grid(row=0, column=0, sticky="nsew")
    root.update_idletasks()
    loading_width = loading_frame.winfo_reqwidth()
    loading_height = loading_frame.winfo_reqheight()
    x = (root.winfo_screenwidth() - loading_width) // 2
    y = (root.winfo_screenheight() - loading_height) // 2
    root.geometry(f"{loading_width}x{loading_height}+{x}+{y}")
    run_button.config(state="disabled")

    # Keep calibration and simulation off the GUI thread so the window stays responsive.
    worker_thread = threading.Thread(
        target=run_simulation_worker,
        args=(
            selected_nodes,
            selected_cities,
            selected_runs,
            selected_difficulty,
            validation_mode,
            selected_host_workers,
            selected_benchmark_runs,
            selected_seed,
        ),
        daemon=True,
    )
    active_thread = worker_thread
    root.after(1200, worker_thread.start)


def run_simulation_worker(
    selected_nodes, selected_cities, selected_runs, selected_difficulty, validation_mode,
    selected_host_workers=1, selected_benchmark_runs=1, selected_seed=20260910,
):
    """Run calibration and simulations off the UI thread, then schedule success or
    error display.
    """
    root.after(0, update_loading_progress, 5, "Starting benchmarks... 5 / 100")
    start = time.perf_counter()
    try:
        from experiments import make_inputs
        with cancellation(cancel_event):
            inputs = make_inputs(selected_seed, selected_runs, selected_cities, selected_nodes)
            main_functions = MainFunctions(
                selected_nodes, selected_cities, selected_runs, selected_difficulty,
                validation_mode, benchmark_progress_callback=benchmark_progress,
                host_workers=selected_host_workers, benchmark_runs=selected_benchmark_runs,
                run_inputs=inputs,
            )
            data = main_functions.run_simulation(progress_callback=simulation_progress)
        elapsed = time.perf_counter() - start
        with open("timing.txt", "a") as f:
            f.write(f"run_settings total: {elapsed:.3f}s\n")

        # Schedule UI updates on the Tkinter event loop.
        root.after(0, simulation_finished, data)
    except Exception as error:
        root.after(0, simulation_failed, error)


def simulation_progress(completed, total):
    """Translate completed simulation runs into the loading-bar progress range."""
    percentage = 25 + completed / total * 75
    root.after(0, update_progress_bar, percentage, completed, total)


def update_progress_bar(percentage, completed, total):
    """Update the displayed progress count and completion percentage."""
    progress_bar["value"] = percentage
    progress_label.config(text=f"Running simulations... {percentage:.0f} / 100")


def benchmark_progress(completed, total, message):
    """Forward calibration progress when a callback was supplied."""
    percentage = 5 + completed / total * 20
    root.after(
        0, update_loading_progress, percentage, f"{message} {percentage:.0f} / 100"
    )


def update_loading_progress(percentage, message):
    """Set the loading bar and its message on the GUI thread."""
    progress_bar["value"] = percentage
    progress_label.config(text=message)


def simulation_finished(data):
    """Store the finished result and switch the interface to the results view."""
    if closing:
        return
    progress_bar["value"] = 100
    progress_label.config(text="Simulation complete! 100 / 100")
    run_button.config(state="normal")
    root.after(500, display_results, data)


def simulation_failed(error):
    """Display a genuine run error and restore controls so the user can try again."""
    if closing:
        return
    progress_bar["value"] = 0
    progress_label.config(text="Simulation failed.")
    if not isinstance(error, SimulationCancelled):
        messagebox.showerror("Simulation failed", str(error))
    loading_frame.grid_remove()
    settings_frame.grid(row=0, column=0, sticky="nsew")
    run_button.config(state="normal")


def display_results(data):
    """Populate summary labels, node details, and comparison charts from returned
    results.
    """
    global normal_geometry
    root.geometry(normal_geometry)
    loading_frame.grid_remove()
    results_container.grid(row=0, column=0, sticky="nsew")
    configuration_nodes_label.config(text=f"Number of Nodes: {nodes.get()}")
    configuration_runs_label.config(text=f"Number of Average Runs: {runs.get()}")
    configuration_difficulty_label.config(
        text=f"PoW Leading Zeroes : {difficulty.get()}"
    )
    configuration_cities_label.config(text=f"Number of TSP Cities: {cities.get()}")
    pow_rates = data["pow"]["average_hash_rate"]
    pouw_rates = data["pouw"]["average_search_rate"]
    average_pow_hash_rate = sum(pow_rates.values()) / len(pow_rates)
    average_pouw_computation_rate = sum(pouw_rates.values()) / len(pouw_rates)
    pow_hash_rate_label.config(text=f"{average_pow_hash_rate:.2f} hashes/sec")
    pouw_computation_rate_label.config(
        text=f"{average_pouw_computation_rate:.2f} computations/sec"
    )
    average_hashes = data["average_hashes"]
    average_computations = data["average_computations"]

    # Reference work uses comparable units; raw hashes and B&B nodes stay separate.
    average_pow_compute_work = data["average_pow_compute_work"]
    average_pouw_compute_work = data["average_pouw_compute_work"]
    average_pow_simulation_time = data["average_pow_simulation_time"]
    average_pouw_simulation_time = data["average_pouw_simulation_time"]
    pow_compute_work_label.config(text=f"{average_pow_compute_work:.4f} s")
    pouw_compute_work_label.config(text=f"{average_pouw_compute_work:.4f} s")
    average_hashes_label.config(text=f"{average_hashes:.2f}")
    average_computations_label.config(text=f"{average_computations:.2f}")
    pow_simulation_time_label.config(text=f"{average_pow_simulation_time:.2f} s")
    pouw_simulation_time_label.config(text=f"{average_pouw_simulation_time:.2f} s")
    show_node_details(data)
    show_comparison_graph(data)
    loading_frame.grid_remove()
    results_container.grid(row=0, column=0, sticky="nsew")
    results_canvas.yview_moveto(0)


def show_node_details(data):
    """Display worker rates, discoverer/finisher attribution, and complete tour
    results.
    """
    for widget in node_frame.winfo_children():
        widget.destroy()
    nodes_per_row = 4
    ttk.Label(node_frame, text="PoW Node Results").grid(
        row=0, column=0, columnspan=nodes_per_row, sticky="w", pady=(0, 10)
    )
    pow_rates = data["pow"]["average_hash_rate"]
    for index, (node_name, hash_rate) in enumerate(pow_rates.items()):
        row = 1 + index // nodes_per_row
        column = index % nodes_per_row
        ttk.Label(
            node_frame, text=f"{node_name}: {hash_rate:.2f} hash/s", width=26
        ).grid(row=row, column=column, padx=10, pady=5, sticky="w")
    pow_rows = (len(pow_rates) + nodes_per_row - 1) // nodes_per_row
    pouw_start_row = 1 + pow_rows + 1
    ttk.Label(node_frame, text="PoUW Node Results").grid(
        row=pouw_start_row,
        column=0,
        columnspan=nodes_per_row,
        sticky="w",
        pady=(20, 10),
    )
    pouw_rates = data["pouw"]["average_search_rate"]
    for index, (node_name, search_rate) in enumerate(pouw_rates.items()):
        row = pouw_start_row + 1 + index // nodes_per_row
        column = index % nodes_per_row
        ttk.Label(
            node_frame, text=f"{node_name}: {search_rate:.2f} computation/s", width=30
        ).grid(row=row, column=column, padx=10, pady=5, sticky="w")
    pow_wins = {}
    for run in data["pow"]["runs"]:
        winner_name = run["winner"]["name"]
        pow_wins[winner_name] = pow_wins.get(winner_name, 0) + 1
    pouw_wins = {}
    for run in data["pouw"]["runs"]:
        winner_name = run["winner"]["name"]
        pouw_wins[winner_name] = pouw_wins.get(winner_name, 0) + 1
    pow_wins = sorted(pow_wins.items(), key=lambda x: x[1], reverse=True)
    pouw_wins = sorted(pouw_wins.items(), key=lambda x: x[1], reverse=True)
    row += 2
    ttk.Label(node_frame, text="PoW Winners").grid(
        row=row, column=0, columnspan=5, sticky="w", pady=(25, 10)
    )
    row += 1
    for run_number, run in enumerate(data["pow"]["runs"], start=1):
        winner = run["winner"]
        ttk.Label(node_frame, text=f"Run {run_number}").grid(
            row=row, column=0, sticky="w", pady=(10, 2)
        )
        row += 1
        ttk.Label(node_frame, text=f"Finishing node: {winner['name']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(node_frame, text=f"Hashes: {winner['hashes']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(node_frame, text=f"Nonce: {winner['nonce']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(node_frame, text=f"Extra nonce: {winner['extra_nonce']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(node_frame, text=f"Hash: {winner['header_hash']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
    ttk.Label(node_frame, text="PoUW Winners").grid(
        row=row, column=0, columnspan=5, sticky="w", pady=(25, 10)
    )
    row += 1
    for run_number, run in enumerate(data["pouw"]["runs"], start=1):
        winner = run["winner"]
        ttk.Label(node_frame, text=f"Run {run_number}").grid(
            row=row, column=0, sticky="w", pady=(10, 2)
        )
        row += 1
        ttk.Label(
            node_frame,
            text=f"Best-tour discoverer: {winner['name']} | Finishing worker: {run['finishing_node']}",
        ).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Label(node_frame, text=f"Path: {winner['path']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(
            node_frame, text=f"Search-node lower bound: {winner['lower_bound']}"
        ).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Label(
            node_frame, text=f"Tour cost (including return): {winner['total_cost']}"
        ).grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Label(node_frame, text=f"Vertex: {winner['vertex']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1
        ttk.Label(node_frame, text=f"Visited: {winner['visited']}").grid(
            row=row, column=0, sticky="w"
        )
        row += 1


def show_comparison_graph(data):
    """Plot normalized work and simulated time with validation components kept
    distinct.
    """
    for widget in comparison_frame.winfo_children():
        widget.destroy()
    average_pow_compute_work = data["average_pow_compute_work"]
    average_pouw_compute_work = data["average_pouw_compute_work"]
    average_validation_compute_work = data["average_validation_compute_work"]
    average_validated_pouw_compute_work = data["average_validated_pouw_compute_work"]
    average_pow_simulation_time = data["average_pow_simulation_time"]
    average_pouw_simulation_time = data["average_pouw_simulation_time"]
    average_validation_time = data["average_validation_time"]
    average_validated_pouw_simulation_time = data[
        "average_validated_pouw_simulation_time"
    ]
    selected_validation = validation.get()
    if selected_validation == "proof":
        validation_name = "PoUW + Proof Validation"
    elif selected_validation == "council":
        validation_name = "PoUW + Council Validation"
    else:
        validation_name = "PoUW"
    if selected_validation == "none":
        main_pouw_work = average_pouw_compute_work
        main_pouw_name = "PoUW"
    else:
        main_pouw_work = average_validated_pouw_compute_work
        main_pouw_name = validation_name
    create_comparison_graph(
        comparison_frame,
        "PoW vs PoUW - Reference Compute Work",
        ["PoW", main_pouw_name],
        [average_pow_compute_work, main_pouw_work],
        "Reference Compute Work [s]",
    )
    if selected_validation == "none":
        main_pouw_time = average_pouw_simulation_time
    else:
        main_pouw_time = average_validated_pouw_simulation_time
    create_comparison_graph(
        comparison_frame,
        "PoW vs PoUW - Simulated Completion Time",
        ["PoW", main_pouw_name],
        [average_pow_simulation_time, main_pouw_time],
        "Simulation Time [s]",
    )
    if selected_validation == "none":
        return
    create_comparison_graph(
        comparison_frame,
        "PoUW Validation Work Breakdown",
        [
            (
                "Search +\ntranscript generation"
                if selected_validation == "proof"
                else "Search"
            ),
            "Validation",
            validation_name,
        ],
        [
            average_pouw_compute_work,
            average_validation_compute_work,
            average_validated_pouw_compute_work,
        ],
        "Reference Compute Work [s]",
    )
    create_comparison_graph(
        comparison_frame,
        "PoUW Validation Time Breakdown",
        [
            (
                "Search +\ntranscript generation"
                if selected_validation == "proof"
                else "Search"
            ),
            "Validation",
            validation_name,
        ],
        [
            average_pouw_simulation_time,
            average_validation_time,
            average_validated_pouw_simulation_time,
        ],
        "Simulation Time [s]",
    )
    if selected_validation == "proof":
        create_benchmark_graph(
            comparison_frame,
            "Proof Validation Benchmark Throughput",
            ["Transcript\nGeneration", "Hash\nValidation", "Semantic\nValidation"],
            [
                MainFunctions.transcript_per_second,
                MainFunctions.hash_validation_per_second,
                MainFunctions.semantic_validation_per_second,
            ],
            ["records/s", "checks/s", "semantic units/s"],
        )


def create_comparison_graph(parent, title, methods, values, ylabel):
    """Embed one labelled bar chart for quantities expressed in the same unit."""
    frame = ttk.LabelFrame(parent, text=title, padding=10)
    frame.pack(fill="both", expand=True, pady=10)
    figure = Figure(figsize=(7, 3), dpi=100)
    ax = figure.add_subplot(111)
    ax.bar(methods, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    figure.tight_layout()
    canvas = FigureCanvasTkAgg(figure, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def create_benchmark_graph(parent, title, methods, values, units):
    """Display operation-specific throughputs with their distinct unit labels."""
    frame = ttk.LabelFrame(parent, text=title, padding=10)
    frame.pack(fill="both", expand=True, pady=10)
    figure = Figure(figsize=(7, 3.5), dpi=100)
    ax = figure.add_subplot(111)
    bars = ax.bar(methods, values)
    ax.set_title(title)
    ax.set_ylabel("Benchmark Throughput")
    for bar, value, unit in zip(bars, values, units):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:,.0f}\n{unit}",
            ha="center",
            va="bottom",
        )
    if values:
        maximum_value = max(values)
        if maximum_value > 0:
            ax.set_ylim(0, maximum_value * 1.2)
    figure.tight_layout()
    canvas = FigureCanvasTkAgg(figure, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def show_settings():
    """Return to the configuration screen and restore the normal window layout."""
    global normal_geometry
    root.geometry(normal_geometry)
    results_container.grid_remove()
    settings_frame.grid(row=0, column=0, sticky="nsew")
    results_container.grid_remove()
    settings_frame.grid(row=0, column=0, sticky="nsew")


def start_gui(default_host_workers=1):
    """Build the settings, progress, and results widgets, then start the Tkinter event
    loop.
    """
    global root
    global normal_geometry
    global settings_frame
    global loading_frame
    global results_container
    global results_canvas
    global results_frame
    global comparison_frame
    global node_frame
    global nodes
    global runs
    global difficulty
    global cities
    global validation
    global configuration_nodes_label
    global configuration_runs_label
    global configuration_difficulty_label
    global configuration_cities_label
    global pow_hash_rate_label
    global pow_average_hashes_label
    global pouw_computation_rate_label
    global pouw_average_computations_label
    global average_hashes_label
    global average_computations_label
    global pow_simulation_time_label
    global pouw_simulation_time_label
    global run_button
    global progress_bar
    global progress_label
    global pow_compute_work_label
    global pouw_compute_work_label
    global host_workers, benchmark_runs, experiment_seed
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", close_application)
    root.title("PoW vs PoUW Simulation")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    settings_frame = ttk.Frame(root, padding=20)
    settings_frame.grid(row=0, column=0, sticky="nsew")
    settings_frame.columnconfigure(0, weight=1)
    settings_frame.columnconfigure(1, weight=1)
    title = ttk.Label(settings_frame, text="PoW vs PoUW Benchmark")
    title.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    benchmark_settings_frame = ttk.LabelFrame(
        settings_frame, text="Benchmark Settings", padding=15
    )
    benchmark_settings_frame.grid(
        row=1, column=0, columnspan=2, sticky="we", pady=(0, 20)
    )
    benchmark_settings_frame.columnconfigure(1, weight=1)
    ttk.Label(benchmark_settings_frame, text="Number of Nodes").grid(
        row=0, column=0, sticky="w", padx=5, pady=10
    )

    # The user-selected minimum remains three workers.
    nodes = tk.IntVar(value=5)
    nodes_value_label = ttk.Label(benchmark_settings_frame, text="5")
    nodes_value_label.grid(row=0, column=2, padx=(10, 5))

    def update_nodes(value):
        """Show the worker-count slider value beside the control."""
        nodes_value_label.config(text=str(int(float(value))))

    nodes_scale = ttk.Scale(
        benchmark_settings_frame,
        from_=3,
        to=20,
        orient="horizontal",
        variable=nodes,
        command=update_nodes,
    )
    nodes_scale.grid(row=0, column=1, sticky="ew", padx=10)
    ttk.Label(benchmark_settings_frame, text="Number of Runs").grid(
        row=1, column=0, sticky="w", padx=5, pady=10
    )
    runs = tk.IntVar(value=3)
    runs_value_label = ttk.Label(benchmark_settings_frame, text="3")
    runs_value_label.grid(row=1, column=2, padx=(10, 5))

    def update_runs(value):
        """Show the repetition-count slider value beside the control."""
        runs_value_label.config(text=str(int(float(value))))

    runs_scale = ttk.Scale(
        benchmark_settings_frame,
        from_=1,
        to=5,
        orient="horizontal",
        variable=runs,
        command=update_runs,
    )
    runs_scale.grid(row=1, column=1, sticky="ew", padx=10)
    pow_settings_frame = ttk.LabelFrame(settings_frame, text="PoW Settings", padding=15)
    pow_settings_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 20))
    pow_settings_frame.columnconfigure(1, weight=1)
    ttk.Label(pow_settings_frame, text="Leading Zeros").grid(
        row=0, column=0, sticky="w", padx=5, pady=10
    )
    difficulty = tk.IntVar(value=4)
    difficulty_value_label = ttk.Label(pow_settings_frame, text="4")
    difficulty_value_label.grid(row=0, column=2, padx=(10, 5))

    def update_difficulty(value):
        """Show the leading-zero difficulty value beside the control."""
        difficulty_value_label.config(text=str(int(float(value))))

    difficulty_scale = ttk.Scale(
        pow_settings_frame,
        from_=1,
        to=8,
        orient="horizontal",
        variable=difficulty,
        command=update_difficulty,
    )
    difficulty_scale.grid(row=0, column=1, sticky="ew", padx=10)
    pouw_settings_frame = ttk.LabelFrame(
        settings_frame, text="PoUW Settings", padding=15
    )
    pouw_settings_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=(0, 20))
    pouw_settings_frame.columnconfigure(1, weight=1)
    ttk.Label(pouw_settings_frame, text="Number of Cities").grid(
        row=0, column=0, sticky="w", padx=5, pady=10
    )

    # The user-selected minimum remains three cities.
    cities = tk.IntVar(value=10)
    cities_value_label = ttk.Label(pouw_settings_frame, text="10")
    cities_value_label.grid(row=0, column=2, padx=(10, 5))

    def update_cities(value):
        """Show the city-count slider value beside the control."""
        cities_value_label.config(text=str(int(float(value))))

    cities_scale = ttk.Scale(
        pouw_settings_frame,
        from_=3,
        to=15,
        orient="horizontal",
        variable=cities,
        command=update_cities,
    )
    cities_scale.grid(row=0, column=1, sticky="ew", padx=10)
    ttk.Label(pouw_settings_frame, text="Verification").grid(
        row=1, column=0, sticky="w", padx=5, pady=10
    )
    verification_frame = ttk.Frame(pouw_settings_frame)
    verification_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=10)
    validation = tk.StringVar(value="none")
    ttk.Radiobutton(
        verification_frame, text="None", variable=validation, value="none"
    ).grid(row=0, column=0, padx=(0, 15))
    ttk.Radiobutton(
        verification_frame, text="Proof Validation", variable=validation, value="proof"
    ).grid(row=0, column=1, padx=15)
    ttk.Radiobutton(
        verification_frame,
        text="Council Validation",
        variable=validation,
        value="council",
    ).grid(row=0, column=2, padx=15)
    controls = ttk.LabelFrame(settings_frame, text="Execution and repeatability", padding=10)
    controls.grid(row=3, column=0, columnspan=2, sticky="we")
    host_workers = tk.IntVar(value=default_host_workers)
    benchmark_runs = tk.IntVar(value=1)
    experiment_seed = tk.StringVar(value="20260910")
    for row, (label, variable) in enumerate([
        ("Real worker processes", host_workers),
        ("Benchmark repetitions", benchmark_runs),
        ("Experiment seed", experiment_seed),
    ]):
        ttk.Label(controls, text=label).grid(row=row, column=0, sticky="w", padx=5)
        ttk.Entry(controls, textvariable=variable, width=15).grid(row=row, column=1)
    ttk.Label(controls, text="Worker limit does not change simulated nodes or impose a CPU percentage cap.", wraplength=420).grid(row=3, column=0, columnspan=2, pady=5)
    run_button = ttk.Button(settings_frame, text="Run", command=run_settings)
    run_button.grid(row=4, column=0, columnspan=2, pady=(10, 10))
    loading_frame = ttk.Frame(root, padding=20)
    loading_frame.columnconfigure(0, weight=1)
    loading_frame.rowconfigure(0, weight=1)
    loading_content_frame = ttk.Frame(loading_frame)
    loading_content_frame.grid(row=0, column=0)
    ttk.Label(loading_content_frame, text="Running Simulation").grid(
        row=0, column=0, pady=(0, 20)
    )
    progress_label = ttk.Label(loading_content_frame, text="Ready")
    progress_label.grid(row=1, column=0, pady=(0, 10))
    progress_bar = ttk.Progressbar(
        loading_content_frame,
        orient="horizontal",
        mode="determinate",
        maximum=100,
        length=400,
    )
    progress_bar.grid(row=2, column=0, pady=(0, 10))
    ttk.Button(loading_content_frame, text="Cancel", command=cancel_event.set).grid(row=3, column=0)
    results_container = ttk.Frame(root)
    results_container.columnconfigure(0, weight=1)
    results_container.rowconfigure(0, weight=1)
    results_canvas = tk.Canvas(results_container, highlightthickness=0)
    results_canvas.grid(row=0, column=0, sticky="nsew")
    results_scrollbar = ttk.Scrollbar(
        results_container, orient="vertical", command=results_canvas.yview
    )
    results_scrollbar.grid(row=0, column=1, sticky="ns")
    results_frame = ttk.Frame(results_canvas, padding=20)
    results_window = results_canvas.create_window(
        (0, 0), window=results_frame, anchor="nw"
    )
    results_canvas.configure(yscrollcommand=results_scrollbar.set)

    def update_scroll_region(event=None):
        """Update the scrollable extent after the results layout changes."""
        results_canvas.configure(scrollregion=results_canvas.bbox("all"))

    def resize_results_frame(event):
        """Match the results frame width to its containing canvas."""
        results_canvas.itemconfigure(results_window, width=event.width)

    results_frame.bind("<Configure>", update_scroll_region)
    results_canvas.bind("<Configure>", resize_results_frame)

    def scroll_results(event):
        """Scroll the results canvas in response to the mouse wheel."""
        results_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    results_canvas.bind("<MouseWheel>", scroll_results)
    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)
    ttk.Label(results_frame, text="Simulation Results").grid(
        row=0, column=0, columnspan=2, pady=(0, 20)
    )
    configuration_frame = ttk.LabelFrame(
        results_frame, text="Configuration", padding=15
    )
    configuration_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 20))
    configuration_nodes_label = ttk.Label(
        configuration_frame, text="Number of Nodes: -"
    )
    configuration_nodes_label.grid(row=0, column=0, padx=15)
    configuration_runs_label = ttk.Label(
        configuration_frame, text="Number of Average Runs: -"
    )
    configuration_runs_label.grid(row=0, column=1, padx=15)
    configuration_difficulty_label = ttk.Label(
        configuration_frame, text="PoW Leading Zeroes : -"
    )
    configuration_difficulty_label.grid(row=0, column=2, padx=15)
    configuration_cities_label = ttk.Label(
        configuration_frame, text="Number of TSP Cities: -"
    )
    configuration_cities_label.grid(row=0, column=3, padx=15)
    benchmark_frame = ttk.LabelFrame(
        results_frame, text="Average Simulated Node Rates", padding=15
    )
    benchmark_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(0, 20))
    ttk.Label(benchmark_frame, text="PoW").grid(
        row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10)
    )
    ttk.Label(benchmark_frame, text="Average Hash Rate:").grid(
        row=1, column=0, sticky="w", padx=15, pady=5
    )
    pow_hash_rate_label = ttk.Label(benchmark_frame, text="- hashes/sec")
    pow_hash_rate_label.grid(row=1, column=1, sticky="e", padx=15, pady=5)
    ttk.Label(benchmark_frame, text="PoUW").grid(
        row=0, column=2, columnspan=2, sticky="w", padx=15, pady=(0, 10)
    )
    ttk.Label(benchmark_frame, text="Average Computation Rate:").grid(
        row=1, column=2, sticky="w", padx=15, pady=5
    )
    pouw_computation_rate_label = ttk.Label(benchmark_frame, text="- computations/sec")
    pouw_computation_rate_label.grid(row=1, column=3, sticky="e", padx=15, pady=5)
    pow_results_frame = ttk.LabelFrame(results_frame, text="Proof of Work", padding=15)
    pow_results_frame.grid(row=3, column=0, sticky="nsew", padx=(0, 10), pady=(0, 20))
    ttk.Label(pow_results_frame, text="Average Hashes Performed:").grid(
        row=0, column=0, sticky="w"
    )
    average_hashes_label = ttk.Label(pow_results_frame, text="-")
    average_hashes_label.grid(row=0, column=1, sticky="e", padx=20)
    ttk.Label(pow_results_frame, text="Reference Compute Work:").grid(
        row=1, column=0, sticky="w"
    )
    pow_compute_work_label = ttk.Label(pow_results_frame, text="-")
    pow_compute_work_label.grid(row=1, column=1, sticky="e", padx=20)
    ttk.Label(pow_results_frame, text="Simulation Time:").grid(
        row=2, column=0, sticky="w"
    )
    pow_simulation_time_label = ttk.Label(pow_results_frame, text="-")
    pow_simulation_time_label.grid(row=2, column=1, sticky="e", padx=20)
    pouw_results_frame = ttk.LabelFrame(
        results_frame, text="Proof of Useful Work", padding=15
    )
    pouw_results_frame.grid(row=3, column=1, sticky="nsew", padx=(10, 0), pady=(0, 20))
    ttk.Label(pouw_results_frame, text="Average B&B Nodes Processed:").grid(
        row=0, column=0, sticky="w"
    )
    average_computations_label = ttk.Label(pouw_results_frame, text="-")
    average_computations_label.grid(row=0, column=1, sticky="e", padx=20)
    ttk.Label(pouw_results_frame, text="Reference Compute Work:").grid(
        row=1, column=0, sticky="w"
    )
    pouw_compute_work_label = ttk.Label(pouw_results_frame, text="-")
    pouw_compute_work_label.grid(row=1, column=1, sticky="e", padx=20)
    ttk.Label(pouw_results_frame, text="Simulation Time:").grid(
        row=2, column=0, sticky="w"
    )
    pouw_simulation_time_label = ttk.Label(pouw_results_frame, text="-")
    pouw_simulation_time_label.grid(row=2, column=1, sticky="e", padx=20)
    comparison_frame = ttk.LabelFrame(results_frame, text="Comparison", padding=15)
    comparison_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(0, 20))
    comparison_frame.columnconfigure(0, weight=1)
    node_frame = ttk.LabelFrame(results_frame, text="Node Details", padding=15)
    node_frame.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 20))
    for column in range(4):
        node_frame.columnconfigure(column, weight=1, minsize=200)
    back_button = ttk.Button(results_frame, text="Back", command=show_settings)
    back_button.grid(row=6, column=0, columnspan=2, pady=(0, 10))
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    normal_geometry = root.geometry()

    # Tkinter now owns the event loop; button callbacks launch subsequent runs.
    root.mainloop()
