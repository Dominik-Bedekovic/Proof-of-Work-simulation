import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from mainFunctions import MainFunctions
import time

# ============================================================
# Validation modes
# ============================================================

NO_VALIDATION = 0
PROOF_VALIDATION = 1
COUNCIL_VALIDATION = 2


# ============================================================
# Global GUI variables
# ============================================================

root = None

settings_frame = None
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


# ============================================================
# Start GUI
# ============================================================

def start_gui():
    global root
    global settings_frame
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

    # ========================================================
    # Main window
    # ========================================================

    root = tk.Tk()

    root.title("PoW vs PoUW Simulation")

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # ========================================================
    # Settings frame
    # ========================================================

    settings_frame = ttk.Frame(
        root,
        padding=20
    )

    settings_frame.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    settings_frame.columnconfigure(0, weight=1)
    settings_frame.columnconfigure(1, weight=1)

    title = ttk.Label(
        settings_frame,
        text="PoW vs PoUW Benchmark"
    )

    title.grid(
        row=0,
        column=0,
        columnspan=2,
        pady=(0, 20)
    )

    # ========================================================
    # Benchmark settings
    # ========================================================

    benchmark_settings_frame = ttk.LabelFrame(
        settings_frame,
        text="Benchmark Settings",
        padding=15
    )

    benchmark_settings_frame.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="we",
        pady=(0, 20)
    )

    benchmark_settings_frame.columnconfigure(1, weight=1)


    # ========================================================
    # Number of Nodes
    # ========================================================

    ttk.Label(
        benchmark_settings_frame,
        text="Number of Nodes"
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=5,
        pady=10
    )

    nodes = tk.IntVar(value=5)

    nodes_value_label = ttk.Label(
        benchmark_settings_frame,
        text="5"
    )

    nodes_value_label.grid(
        row=0,
        column=2,
        padx=(10, 5)
    )


    def update_nodes(value):
        nodes_value_label.config(
            text=str(int(float(value)))
        )


    nodes_scale = ttk.Scale(
        benchmark_settings_frame,
        from_=1,
        to=20,
        orient="horizontal",
        variable=nodes,
        command=update_nodes
    )

    nodes_scale.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=10
    )


    # ========================================================
    # Number of Runs
    # ========================================================

    ttk.Label(
        benchmark_settings_frame,
        text="Number of Runs"
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=5,
        pady=10
    )

    runs = tk.IntVar(value=3)

    runs_value_label = ttk.Label(
        benchmark_settings_frame,
        text="3"
    )

    runs_value_label.grid(
        row=1,
        column=2,
        padx=(10, 5)
    )


    def update_runs(value):
        runs_value_label.config(
            text=str(int(float(value)))
        )


    runs_scale = ttk.Scale(
        benchmark_settings_frame,
        from_=1,
        to=5,
        orient="horizontal",
        variable=runs,
        command=update_runs
    )

    runs_scale.grid(
        row=1,
        column=1,
        sticky="ew",
        padx=10
    )


    # ========================================================
    # PoW settings
    # ========================================================

    pow_settings_frame = ttk.LabelFrame(
        settings_frame,
        text="PoW Settings",
        padding=15
    )

    pow_settings_frame.grid(
        row=2,
        column=0,
        sticky="nsew",
        padx=(0, 10),
        pady=(0, 20)
    )

    pow_settings_frame.columnconfigure(
        1,
        weight=1
    )


    # ========================================================
    # Leading zeros
    # ========================================================

    ttk.Label(
        pow_settings_frame,
        text="Leading Zeros"
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=5,
        pady=10
    )

    difficulty = tk.IntVar(value=4)

    difficulty_value_label = ttk.Label(
        pow_settings_frame,
        text="4"
    )

    difficulty_value_label.grid(
        row=0,
        column=2,
        padx=(10, 5)
    )


    def update_difficulty(value):
        difficulty_value_label.config(
            text=str(int(float(value)))
        )


    difficulty_scale = ttk.Scale(
        pow_settings_frame,
        from_=1,
        to=8,
        orient="horizontal",
        variable=difficulty,
        command=update_difficulty
    )

    difficulty_scale.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=10
    )


    # ========================================================
    # PoUW settings
    # ========================================================

    pouw_settings_frame = ttk.LabelFrame(
        settings_frame,
        text="PoUW Settings",
        padding=15
    )

    pouw_settings_frame.grid(
        row=2,
        column=1,
        sticky="nsew",
        padx=(10, 0),
        pady=(0, 20)
    )

    pouw_settings_frame.columnconfigure(
        1,
        weight=1
    )


    # ========================================================
    # Number of cities
    # ========================================================

    ttk.Label(
        pouw_settings_frame,
        text="Number of Cities"
    ).grid(
        row=0,
        column=0,
        sticky="w",
        padx=5,
        pady=10
    )

    cities = tk.IntVar(value=10)

    cities_value_label = ttk.Label(
        pouw_settings_frame,
        text="10"
    )

    cities_value_label.grid(
        row=0,
        column=2,
        padx=(10, 5)
    )


    def update_cities(value):
        cities_value_label.config(
            text=str(int(float(value)))
        )


    cities_scale = ttk.Scale(
        pouw_settings_frame,
        from_=3,
        to=15,
        orient="horizontal",
        variable=cities,
        command=update_cities
    )

    cities_scale.grid(
        row=0,
        column=1,
        sticky="ew",
        padx=10
    )


    # ========================================================
    # Verification
    # ========================================================

    ttk.Label(
        pouw_settings_frame,
        text="Verification"
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=5,
        pady=10
    )

    verification_frame = ttk.Frame(
        pouw_settings_frame
    )

    verification_frame.grid(
        row=1,
        column=1,
        columnspan=2,
        sticky="w",
        padx=10
    )

    validation = tk.StringVar(value="none")

    ttk.Radiobutton(
        verification_frame,
        text="None",
        variable=validation,
        value="none"
    ).grid(
        row=0,
        column=0,
        padx=(0, 15)
    )

    ttk.Radiobutton(
        verification_frame,
        text="Proof Validation",
        variable=validation,
        value="proof"
    ).grid(
        row=0,
        column=1,
        padx=15
    )

    ttk.Radiobutton(
        verification_frame,
        text="Council Validation",
        variable=validation,
        value="council"
    ).grid(
        row=0,
        column=2,
        padx=15
    )

    # ========================================================
    # Run button
    # ========================================================

    run_button = ttk.Button(
        settings_frame,
        text="Run",
        command=run_settings
    )

    run_button.grid(
        row=3,
        column=0,
        columnspan=2,
        pady=(10, 20)
    )

    # ========================================================
    # Results container
    # ========================================================

    results_container = ttk.Frame(
        root
    )

    results_container.columnconfigure(
        0,
        weight=1
    )

    results_container.rowconfigure(
        0,
        weight=1
    )

    # ========================================================
    # Results canvas
    # ========================================================

    results_canvas = tk.Canvas(
        results_container,
        highlightthickness=0
    )

    results_canvas.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    # ========================================================
    # Scrollbar
    # ========================================================

    results_scrollbar = ttk.Scrollbar(
        results_container,
        orient="vertical",
        command=results_canvas.yview
    )

    results_scrollbar.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    # ========================================================
    # Scrollable results frame
    # ========================================================

    results_frame = ttk.Frame(
        results_canvas,
        padding=20
    )

    results_window = results_canvas.create_window(
        (0, 0),
        window=results_frame,
        anchor="nw"
    )

    results_canvas.configure(
        yscrollcommand=results_scrollbar.set
    )

    def update_scroll_region(event=None):
        results_canvas.configure(
            scrollregion=results_canvas.bbox("all")
        )

    def resize_results_frame(event):
        results_canvas.itemconfigure(
            results_window,
            width=event.width
        )

    results_frame.bind(
        "<Configure>",
        update_scroll_region
    )

    results_canvas.bind(
        "<Configure>",
        resize_results_frame
    )

    def scroll_results(event):
        results_canvas.yview_scroll(
            int(-1 * (event.delta / 120)),
            "units"
        )

    results_canvas.bind(
        "<MouseWheel>",
        scroll_results
    )

    # ========================================================
    # Results layout
    # ========================================================

    results_frame.columnconfigure(0, weight=1)
    results_frame.columnconfigure(1, weight=1)

    ttk.Label(
        results_frame,
        text="Simulation Results"
    ).grid(
        row=0,
        column=0,
        columnspan=2,
        pady=(0, 20)
    )

    # ========================================================
    # Configuration
    # ========================================================

    configuration_frame = ttk.LabelFrame(
        results_frame,
        text="Configuration",
        padding=15
    )

    configuration_frame.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="we",
        pady=(0, 20)
    )

    configuration_nodes_label = ttk.Label(
        configuration_frame,
        text="Number of Nodes: -"
    )

    configuration_nodes_label.grid(
        row=0,
        column=0,
        padx=15
    )

    configuration_runs_label = ttk.Label(
        configuration_frame,
        text="Number of Average Runs: -"
    )

    configuration_runs_label.grid(
        row=0,
        column=1,
        padx=15
    )

    configuration_difficulty_label = ttk.Label(
        configuration_frame,
        text="PoW Leading Zeroes : -"
    )

    configuration_difficulty_label.grid(
        row=0,
        column=2,
        padx=15
    )

    configuration_cities_label = ttk.Label(
        configuration_frame,
        text="Number of TSP Cities: -"
    )

    configuration_cities_label.grid(
        row=0,
        column=3,
        padx=15
    )

    # ========================================================
    # Benchmark
    # ========================================================

    benchmark_frame = ttk.LabelFrame(
        results_frame,
        text="Benchmark Speed Results",
        padding=15
    )

    benchmark_frame.grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="we",
        pady=(0, 20)
    )

    # --------------------------------------------------------
    # PoW benchmark
    # --------------------------------------------------------

    ttk.Label(
        benchmark_frame,
        text="PoW"
    ).grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="w",
        padx=15,
        pady=(0, 10)
    )

    ttk.Label(
        benchmark_frame,
        text="Average Hash Rate:"
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=15,
        pady=5
    )

    pow_hash_rate_label = ttk.Label(
        benchmark_frame,
        text="- hashes/sec"
    )

    pow_hash_rate_label.grid(
        row=1,
        column=1,
        sticky="e",
        padx=15,
        pady=5
    )

    # --------------------------------------------------------
    # PoUW benchmark
    # --------------------------------------------------------

    ttk.Label(
        benchmark_frame,
        text="PoUW"
    ).grid(
        row=0,
        column=2,
        columnspan=2,
        sticky="w",
        padx=15,
        pady=(0, 10)
    )

    ttk.Label(
        benchmark_frame,
        text="Average Computation Rate:"
    ).grid(
        row=1,
        column=2,
        sticky="w",
        padx=15,
        pady=5
    )

    pouw_computation_rate_label = ttk.Label(
        benchmark_frame,
        text="- computations/sec"
    )

    pouw_computation_rate_label.grid(
        row=1,
        column=3,
        sticky="e",
        padx=15,
        pady=5
    )

    # ========================================================
    # PoW results
    # ========================================================

    pow_results_frame = ttk.LabelFrame(
        results_frame,
        text="Proof of Work",
        padding=15
    )

    pow_results_frame.grid(
        row=3,
        column=0,
        sticky="nsew",
        padx=(0, 10),
        pady=(0, 20)
    )

    ttk.Label(
        pow_results_frame,
        text="Total Hashes Performed:"
    ).grid(
        row=0,
        column=0,
        sticky="w"
    )

    average_hashes_label = ttk.Label(
        pow_results_frame,
        text="-"
    )

    average_hashes_label.grid(
        row=0,
        column=1,
        sticky="e",
        padx=20
    )

    ttk.Label(
        pow_results_frame,
        text="Simulation Time:"
    ).grid(
        row=1,
        column=0,
        sticky="w"
    )

    pow_simulation_time_label = ttk.Label(
        pow_results_frame,
        text="-"
    )
    pow_simulation_time_label.grid(
        row=1,
        column=1,
        sticky="e",
        padx=20
    )

    # ========================================================
    # PoUW results
    # ========================================================

    pouw_results_frame = ttk.LabelFrame(
        results_frame,
        text="Proof of Useful Work",
        padding=15
    )

    pouw_results_frame.grid(
        row=3,
        column=1,
        sticky="nsew",
        padx=(10, 0),
        pady=(0, 20)
    )

    ttk.Label(
        pouw_results_frame,
        text="Total Computations Performed:"
    ).grid(
        row=0,
        column=0,
        sticky="w"
    )

    average_computations_label = ttk.Label(
        pouw_results_frame,
        text="-"
    )

    average_computations_label.grid(
        row=0,
        column=1,
        sticky="e",
        padx=20
    )

    ttk.Label(
        pouw_results_frame,
        text="Simulation Time:"
    ).grid(
        row=1,
        column=0,
        sticky="w"
    )

    pouw_simulation_time_label = ttk.Label(
        pouw_results_frame,
        text="-"
    )
    pouw_simulation_time_label.grid(
        row=1,
        column=1,
        sticky="e",
        padx=20
    )

    # ========================================================
    # Comparison
    # ========================================================

    comparison_frame = ttk.LabelFrame(
        results_frame,
        text="Comparison",
        padding=15
    )

    comparison_frame.grid(
        row=4,
        column=0,
        columnspan=2,
        sticky="nsew",
        pady=(0, 20)
    )

    comparison_frame.columnconfigure(
        0,
        weight=1
    )

    # ========================================================
    # Node details
    # ========================================================

    node_frame = ttk.LabelFrame(
        results_frame,
        text="Node Details",
        padding=15
    )

    node_frame.grid(
        row=5,
        column=0,
        columnspan=2,
        sticky="we",
        pady=(0, 20)
    )

    for column in range(4):
        node_frame.columnconfigure(
        column,
        weight=1,
        minsize=200
    )

    # ========================================================
    # Back button
    # ========================================================

    back_button = ttk.Button(
        results_frame,
        text="Back",
        command=show_settings
    )

    back_button.grid(
        row=6,
        column=0,
        columnspan=2,
        pady=(0, 10)
    )

    # ========================================================
    # Center window
    # ========================================================

    root.update_idletasks()

    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()

    x = (
        root.winfo_screenwidth() - width
    ) // 2

    y = (
        root.winfo_screenheight() - height
    ) // 2

    root.geometry(
        f"{width}x{height}+{x}+{y}"
    )

    # ========================================================
    # Start Tkinter
    # ========================================================

    root.mainloop()


# ============================================================
# Run settings
# ============================================================

def run_settings():

    start = time.perf_counter()
    # --------------------------------------------------------
    # Convert validation selection
    # --------------------------------------------------------

    if validation.get() == "none":
        validation_mode = NO_VALIDATION

    elif validation.get() == "proof":
        validation_mode = PROOF_VALIDATION

    elif validation.get() == "council":
        validation_mode = COUNCIL_VALIDATION

    else:
        validation_mode = NO_VALIDATION

    # --------------------------------------------------------
    # Create MainFunctions
    # --------------------------------------------------------

    main_functions = MainFunctions(
        nodes.get(),
        cities.get(),
        runs.get(),
        difficulty.get(),
        validation_mode
    )

    # --------------------------------------------------------
    # Run simulation
    # --------------------------------------------------------

    #print(">>> BEFORE run_simulation()", flush=True)

    data = main_functions.run_simulation()

    elapsed = time.perf_counter() - start

    with open("timinx.txt", "a") as f:
        f.write(f"run_settings total: {elapsed:.3f}s\n")

    #print(">>> AFTER run_simulation()", flush=True)

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    display_results(data)


# ============================================================
# Display simulation results
# ============================================================

def display_results(data):

    configuration_nodes_label.config(
        text=f"Number of Nodes: {nodes.get()}"
    )

    configuration_runs_label.config(
        text=f"Number of Average Runs: {runs.get()}"
    )

    configuration_difficulty_label.config(
        text=f"PoW Leading Zeroes: {difficulty.get()}"
    )

    configuration_cities_label.config(
        text=f"Number of TSP Cities: {cities.get()}"
    )

    # --------------------------------------------------------
    # Benchmark speed
    # --------------------------------------------------------

    pow_rates = data["pow"]["average_hash_rate"]
    pouw_rates = data["pouw"]["average_search_rate"]

    average_pow_hash_rate = (
        sum(pow_rates.values())
        / len(pow_rates)
    )

    average_pouw_computation_rate = (
        sum(pouw_rates.values())
        / len(pouw_rates)
    )

    pow_hash_rate_label.config(
        text=f"{average_pow_hash_rate:.2f} hashes/sec"
    )

    pouw_computation_rate_label.config(
        text=f"{average_pouw_computation_rate:.2f} computations/sec"
    )

    # --------------------------------------------------------
    # Total computational work
    # --------------------------------------------------------

    average_hashes = data["average_hashes"]
    average_computations = data["average_computations"]
    average_pow_simulation_time = data["average_pow_simulation_time"]
    average_pouw_simulation_time = data["average_pouw_simulation_time"]

    average_hashes_label.config(
        text=f"{average_hashes:.2f}"
    )

    average_computations_label.config(
        text=f"{average_computations:.2f}"
    )

    pow_simulation_time_label.config(
        text=f"{average_pow_simulation_time:.2f} s"
    )

    pouw_simulation_time_label.config(
        text=f"{average_pouw_simulation_time:.2f} s"
    )

    # --------------------------------------------------------
    # Node details
    # --------------------------------------------------------

    #print(">>> BEFORE show_node_details()", flush=True)

    show_node_details(data)

    #print(">>> AFTER show_node_details()", flush=True)

    # --------------------------------------------------------
    # Comparison graph
    # --------------------------------------------------------

    #print(">>> BEFORE show_comparison_graph()", flush=True)

    show_comparison_graph(data)

    #print(">>> AFTER show_comparison_graph()", flush=True)

    # --------------------------------------------------------
    # Switch screens
    # --------------------------------------------------------

    #print(">>> BEFORE grid_remove()", flush=True)

    settings_frame.grid_remove()

    #print(">>> AFTER grid_remove()", flush=True)

    results_container.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    #print(">>> AFTER results_container.grid()", flush=True)

    results_canvas.yview_moveto(0)

    #print(">>> AFTER yview_moveto()", flush=True)

# ============================================================
# Node details
# ============================================================

def show_node_details(data):


    # --------------------------------------------------------
    # Remove previous node details
    # --------------------------------------------------------

    for widget in node_frame.winfo_children():
        widget.destroy()

    # ========================================================
    # Layout settings
    # ========================================================

    nodes_per_row = 5

    # ========================================================
    # PoW node results
    # ========================================================

    ttk.Label(
        node_frame,
        text="PoW Node Results"
    ).grid(
        row=0,
        column=0,
        columnspan=nodes_per_row,
        sticky="w",
        pady=(0, 10)
    )

    pow_rates = data["pow"]["average_hash_rate"]

    for index, (node_name, hash_rate) in enumerate(
        pow_rates.items()
    ):

        row = 1 + index // nodes_per_row
        column = index % nodes_per_row

        ttk.Label(
            node_frame,
            text=(
                f"{node_name}: "
                f"{hash_rate:.2f} hashes/sec"
            ),
            width=26
        ).grid(
            row=row,
            column=column,
            padx=10,
            pady=5,
            sticky="w"
        )



    # ========================================================
    # PoUW node results
    # ========================================================

    pow_rows = (
        (len(pow_rates) + nodes_per_row - 1)
        // nodes_per_row
    )

    pouw_start_row = 1 + pow_rows + 1

    ttk.Label(
        node_frame,
        text="PoUW Node Results"
    ).grid(
        row=pouw_start_row,
        column=0,
        columnspan=nodes_per_row,
        sticky="w",
        pady=(20, 10)
    )

    pouw_rates = data["pouw"]["average_search_rate"]

    for index, (node_name, search_rate) in enumerate(
        pouw_rates.items()
    ):

        row = (
            pouw_start_row
            + 1
            + index // nodes_per_row
        )

        column = index % nodes_per_row

        ttk.Label(
            node_frame,
            text=(
                f"{node_name}: "
                f"{search_rate:.2f} computations/sec"
            ),
            width=30
        ).grid(
            row=row,
            column=column,
            padx=10,
            pady=5,
            sticky="w"
        )

    # ========================================================
    # Calculate PoW winner counts
    # ========================================================

    pow_wins = {}

    for run in data["pow"]["runs"]:

        winner_name = run["winner"]["name"]

        pow_wins[winner_name] = (
            pow_wins.get(winner_name, 0) + 1
        )

    # ========================================================
    # Calculate PoUW winner counts
    # ========================================================

    pouw_wins = {}

    for run in data["pouw"]["runs"]:
        winner_name = run["winner"]["name"]

        pouw_wins[winner_name] = (
            pouw_wins.get(winner_name, 0) + 1
        )

    # ========================================================
    # Sort winners by number of wins
    # ========================================================

    pow_wins = sorted(
        pow_wins.items(),
        key=lambda x: x[1],
        reverse=True
    )

    pouw_wins = sorted(
        pouw_wins.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # --------------------------------------------------------
    # PoW winners
    # --------------------------------------------------------

    row += 2

    ttk.Label(
        node_frame,
        text="PoW Winners"
    ).grid(
        row=row,
        column=0,
        columnspan=5,
        sticky="w",
        pady=(25, 10)
    )

    row += 1

    for run_number, run in enumerate(
        data["pow"]["runs"],
        start=1
    ):

        winner = run["winner"]

        ttk.Label(
            node_frame,
            text=f"Run {run_number}"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(10, 2)
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Finishing node: "
                f"{winner['name']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Hashes: "
                f"{winner['hashes']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Nonce: "
                f"{winner['nonce']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Extra nonce: "
                f"{winner['extra_nonce']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Hash: "
                f"{winner['header_hash']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

    # --------------------------------------------------------
    # PoUW winners
    # --------------------------------------------------------

    ttk.Label(
        node_frame,
        text="PoUW Winners"
    ).grid(
        row=row,
        column=0,
        columnspan=5,
        sticky="w",
        pady=(25, 10)
    )

    row += 1

    for run_number, run in enumerate(
        data["pouw"]["runs"],
        start=1
    ):

        winner = run["winner"]

        ttk.Label(
            node_frame,
            text=f"Run {run_number}"
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(10, 2)
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Winning TSP node: "
                f"{winner['name']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Path: "
                f"{winner['path']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Cost: "
                f"{winner['cost']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Total cost: "
                f"{winner['total_cost']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Vertex: "
                f"{winner['vertex']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

        ttk.Label(
            node_frame,
            text=(
                f"Visited: "
                f"{winner['visited']}"
            )
        ).grid(
            row=row,
            column=0,
            sticky="w"
        )

        row += 1

# ============================================================
# Comparison graph
# ============================================================

def show_comparison_graph(data):

    # --------------------------------------------------------
    # Remove previous graphs
    # --------------------------------------------------------

    for widget in comparison_frame.winfo_children():
        widget.destroy()

    # --------------------------------------------------------
    # Baseline PoW and PoUW
    # --------------------------------------------------------

    average_hashes = data["average_hashes"]

    average_computations = data["average_computations"]

    # --------------------------------------------------------
    # Graph 1: PoW vs PoUW
    # --------------------------------------------------------

    create_comparison_graph(
        comparison_frame,
        "PoW vs PoUW",
        [
            "PoW",
            "PoUW"
        ],
        [
            average_hashes,
            average_computations
        ],
        "Computational Work"
    )

    # --------------------------------------------------------
    # Graph 2: PoUW vs PoUW + Validation
    # --------------------------------------------------------

    selected_validation = validation.get()

    if selected_validation == "none":
        return

    validated_computations = (
        data["validated_pouw"]["average_computations"]
    )

    if selected_validation == "proof":

        validation_name = "PoUW + Proof Validation"

    elif selected_validation == "council":

        validation_name = "PoUW + Council Validation"

    else:

        return

    create_comparison_graph(
        comparison_frame,
        "PoUW Validation Comparison",
        [
            "PoUW",
            validation_name
        ],
        [
            average_computations,
            validated_computations
        ],
        "Computational Work"
    )

def create_comparison_graph(
    parent,
    title,
    methods,
    values,
    ylabel
):

    frame = ttk.LabelFrame(
        parent,
        text=title,
        padding=10
    )

    frame.pack(
        fill="both",
        expand=True,
        pady=10
    )

    figure = Figure(
        figsize=(7, 3),
        dpi=100
    )

    ax = figure.add_subplot(111)

    ax.bar(
        methods,
        values
    )

    ax.set_title(
        title
    )

    ax.set_ylabel(
        ylabel
    )

    figure.tight_layout()

    canvas = FigureCanvasTkAgg(
        figure,
        master=frame
    )

    canvas.draw()

    canvas.get_tk_widget().pack(
        fill="both",
        expand=True
    )

# ============================================================
# Return to settings
# ============================================================

def show_settings():

    results_container.grid_remove()

    settings_frame.grid(
        row=0,
        column=0,
        sticky="nsew"
    )