import tkinter as tk
from tkinter import ttk

from mainFunctions import MainFunctions

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


NO_VALIDATION = 0
PROOF_VALIDATION = 1
COUNCIL_VALIDATION = 2

def run_settings():

    num_of_nodes = nodes.get()
    num_of_runs = runs.get()
    num_of_cities = cities.get()
    block_hash_difficulty = difficulty.get()

    # ---------------------------------------------
    # Determine which validation mode was selected
    # ---------------------------------------------

    if validation.get() == "none":
        selected_validation = NO_VALIDATION

    elif validation.get() == "proof":
        selected_validation = PROOF_VALIDATION

    elif validation.get() == "council":
        selected_validation = COUNCIL_VALIDATION

    # ---------------------------------------------
    # Always run the baseline first
    # ---------------------------------------------

    validation_modes = [NO_VALIDATION]

    if selected_validation != NO_VALIDATION:
        validation_modes.append(selected_validation)

    # ---------------------------------------------
    # Run simulations
    # ---------------------------------------------

    results = []

    for validation_mode in validation_modes:

        simulation = MainFunctions(
            num_of_nodes,
            num_of_cities,
            num_of_runs,
            block_hash_difficulty,
            validation_mode
        )

        average_hashes, average_computations = (
            simulation.run_simulation()
        )

        results.append(
            (
                validation_mode,
                average_hashes,
                average_computations
            )
        )

    # ---------------------------------------------
    # Baseline result
    # ---------------------------------------------

    no_validation_result = results[0]

    no_validation_hashes = no_validation_result[1]
    no_validation_computations = no_validation_result[2]

    # ---------------------------------------------
    # Update main result numbers
    # ---------------------------------------------

    average_hashes_label.config(
        text=f"{no_validation_hashes:,.2f}"
    )

    average_computations_label.config(
        text=f"{no_validation_computations:,.2f}"
    )

    # ---------------------------------------------
    # Update configuration labels
    # ---------------------------------------------

    configuration_nodes_label.config(
        text=f"Nodes: {num_of_nodes}"
    )

    configuration_runs_label.config(
        text=f"Runs: {num_of_runs}"
    )

    configuration_difficulty_label.config(
        text=f"PoW Difficulty: {block_hash_difficulty}"
    )

    configuration_cities_label.config(
        text=f"Cities: {num_of_cities}"
    )

    # ---------------------------------------------
    # Create graphs
    # ---------------------------------------------

    show_comparison_graph(results)

    settings_frame.grid_remove()
    results_container.grid()

def show_comparison_graph(results):

    # Remove any previous graphs.
    for widget in comparison_frame.winfo_children():
        widget.destroy()

    no_validation = results[0]

    no_validation_hashes = no_validation[1]
    no_validation_computations = no_validation[2]

    validation_results = results[1:]

    # Always show the baseline.
    create_comparison_graph(
        comparison_frame,
        "No Validation",
        no_validation_hashes,
        no_validation_computations
    )

    # Show a separate comparison for every selected validator.
    for (
        validation_mode,
        average_hashes,
        average_computations
    ) in validation_results:

        if validation_mode == PROOF_VALIDATION:
            title = "Proof Validation"

        elif validation_mode == COUNCIL_VALIDATION:
            title = "Council Validation"

        else:
            continue

        create_validation_comparison_graph(
            comparison_frame,
            title,
            no_validation_hashes,
            no_validation_computations,
            average_hashes,
            average_computations
        )


def create_comparison_graph(
    parent,
    title,
    average_hashes,
    average_computations
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

    methods = [
        "PoW",
        "PoUW"
    ]

    values = [
        average_hashes,
        average_computations
    ]

    ax.bar(
        methods,
        values
    )

    ax.set_title(
        "PoW vs PoUW"
    )

    ax.set_ylabel(
        "Computational Work"
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


def create_validation_comparison_graph(
    parent,
    title,
    no_validation_hashes,
    no_validation_computations,
    validation_hashes,
    validation_computations
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
        figsize=(9, 3),
        dpi=100
    )

    ax1 = figure.add_subplot(121)
    ax2 = figure.add_subplot(122)

    methods = [
        "PoW",
        "PoUW"
    ]

    # -------------------------
    # No validation
    # -------------------------

    values = [
        no_validation_hashes,
        no_validation_computations
    ]

    ax1.bar(
        methods,
        values
    )

    ax1.set_title(
        "No Validation"
    )

    ax1.set_ylabel(
        "Computational Work"
    )

    # -------------------------
    # Validation
    # -------------------------

    values = [
        validation_hashes,
        validation_computations
    ]

    ax2.bar(
        methods,
        values
    )

    ax2.set_title(
        title
    )

    ax2.set_ylabel(
        "Computational Work"
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
# Main window
# ============================================================

root = tk.Tk()

root.title("PoW vs PoUW Simulation")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)


# ============================================================
# Settings frame
# ============================================================

settings_frame = ttk.Frame(
    root,
    padding=20
)

settings_frame.grid(
    column=0,
    row=0,
    sticky="wnes"
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


# ============================================================
# Benchmark settings
# ============================================================

benchmark_frame = ttk.LabelFrame(
    settings_frame,
    text="Benchmark settings",
    padding=15
)

benchmark_frame.grid(
    row=1,
    column=0,
    columnspan=2,
    sticky="we",
    pady=(0, 20)
)

benchmark_frame.columnconfigure(1, weight=1)


ttk.Label(
    benchmark_frame,
    text="Number of Nodes"
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=5,
    pady=10
)


nodes_frame = ttk.Frame(
    benchmark_frame
)

nodes_frame.grid(
    row=0,
    column=1,
    sticky="w",
    padx=10
)


nodes = tk.IntVar(
    value=4
)


ttk.Radiobutton(
    nodes_frame,
    text="3",
    variable=nodes,
    value=3
).grid(
    row=0,
    column=0,
    padx=15
)

ttk.Radiobutton(
    nodes_frame,
    text="4",
    variable=nodes,
    value=4
).grid(
    row=0,
    column=1,
    padx=15
)

ttk.Radiobutton(
    nodes_frame,
    text="5",
    variable=nodes,
    value=5
).grid(
    row=0,
    column=2,
    padx=15
)


ttk.Label(
    benchmark_frame,
    text="Number of Runs"
).grid(
    row=1,
    column=0,
    sticky="w",
    padx=5,
    pady=10
)


runs_frame = ttk.Frame(
    benchmark_frame
)

runs_frame.grid(
    row=1,
    column=1,
    sticky="w",
    padx=10
)


runs = tk.IntVar(
    value=10
)


ttk.Radiobutton(
    runs_frame,
    text="5",
    variable=runs,
    value=5
).grid(
    row=0,
    column=0,
    padx=15
)

ttk.Radiobutton(
    runs_frame,
    text="10",
    variable=runs,
    value=10
).grid(
    row=0,
    column=1,
    padx=15
)

ttk.Radiobutton(
    runs_frame,
    text="20",
    variable=runs,
    value=20
).grid(
    row=0,
    column=2,
    padx=15
)


# ============================================================
# PoW settings
# ============================================================

pow_settings_frame = ttk.LabelFrame(
    settings_frame,
    text="PoW Settings",
    padding=15
)

pow_settings_frame.grid(
    row=2,
    column=0,
    sticky="nesw",
    padx=(0, 10),
    pady=(0, 20)
)

pow_settings_frame.columnconfigure(
    1,
    weight=1
)


ttk.Label(
    pow_settings_frame,
    text="Difficulty"
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=5,
    pady=10
)


difficulty_frame = ttk.Frame(
    pow_settings_frame
)

difficulty_frame.grid(
    row=0,
    column=1,
    sticky="w",
    padx=10
)


difficulty = tk.IntVar(
    value=4
)


ttk.Radiobutton(
    difficulty_frame,
    text="Low",
    variable=difficulty,
    value=2
).grid(
    row=0,
    column=0,
    padx=15
)

ttk.Radiobutton(
    difficulty_frame,
    text="Medium",
    variable=difficulty,
    value=4
).grid(
    row=0,
    column=1,
    padx=15
)

ttk.Radiobutton(
    difficulty_frame,
    text="High",
    variable=difficulty,
    value=6
).grid(
    row=0,
    column=2,
    padx=15
)


# ============================================================
# PoUW settings
# ============================================================

pouw_settings_frame = ttk.LabelFrame(
    settings_frame,
    text="PoUW Settings",
    padding=15
)

pouw_settings_frame.grid(
    row=2,
    column=1,
    sticky="nesw",
    padx=(10, 0),
    pady=(0, 20)
)

pouw_settings_frame.columnconfigure(
    1,
    weight=1
)


ttk.Label(
    pouw_settings_frame,
    text="Number of Cities",
    width=18
).grid(
    row=0,
    column=0,
    sticky="w",
    padx=5,
    pady=10
)


cities_frame = ttk.Frame(
    pouw_settings_frame
)

cities_frame.grid(
    row=0,
    column=1,
    sticky="w",
    padx=10
)


cities = tk.IntVar(
    value=9
)


ttk.Radiobutton(
    cities_frame,
    text="7",
    variable=cities,
    value=7
).grid(
    row=0,
    column=0,
    padx=15
)

ttk.Radiobutton(
    cities_frame,
    text="9",
    variable=cities,
    value=9
).grid(
    row=0,
    column=1,
    padx=15
)

ttk.Radiobutton(
    cities_frame,
    text="11",
    variable=cities,
    value=11
).grid(
    row=0,
    column=2,
    padx=15
)


ttk.Label(
    pouw_settings_frame,
    text="Verification",
    width=18
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
    sticky="w",
    padx=10
)

validation = tk.StringVar(
    value="none"
)

ttk.Radiobutton(
    verification_frame,
    text="None",
    variable=validation,
    value="none"
).grid(
    row=0,
    column=0,
    padx=15
)

ttk.Radiobutton(
    verification_frame,
    text="Proof validation",
    variable=validation,
    value="proof"
).grid(
    row=0,
    column=1,
    padx=15
)

ttk.Radiobutton(
    verification_frame,
    text="Council validation",
    variable=validation,
    value="council"
).grid(
    row=0,
    column=2,
    padx=15
)


# ============================================================
# Run button
# ============================================================

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


# ============================================================
# Results container
# ============================================================

results_container = ttk.Frame(
    root
)

results_container.grid_remove()

results_container.columnconfigure(
    0,
    weight=1
)

results_container.rowconfigure(
    0,
    weight=1
)


# ============================================================
# Results canvas
# ============================================================

results_canvas = tk.Canvas(
    results_container,
    highlightthickness=0
)

results_canvas.grid(
    row=0,
    column=0,
    sticky="nsew"
)


# ============================================================
# Scrollbar
# ============================================================

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


# ============================================================
# Scrollable results frame
# ============================================================

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


results_canvas.bind_all(
    "<MouseWheel>",
    scroll_results
)


# ============================================================
# Results layout
# ============================================================

results_frame.columnconfigure(
    0,
    weight=1
)

results_frame.columnconfigure(
    1,
    weight=1
)


ttk.Label(
    results_frame,
    text="Simulation Results"
).grid(
    row=0,
    column=0,
    columnspan=2,
    pady=(0, 20)
)


# ============================================================
# Configuration
# ============================================================

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
    text=f"Nodes: {nodes.get()}"
)

configuration_nodes_label.grid(
    row=0,
    column=0,
    padx=15
)


configuration_runs_label = ttk.Label(
    configuration_frame,
    text=f"Runs: {runs.get()}"
)

configuration_runs_label.grid(
    row=0,
    column=1,
    padx=15
)


configuration_difficulty_label = ttk.Label(
    configuration_frame,
    text=f"PoW Difficulty: {difficulty.get()}"
)

configuration_difficulty_label.grid(
    row=0,
    column=2,
    padx=15
)


configuration_cities_label = ttk.Label(
    configuration_frame,
    text=f"Cities: {cities.get()}"
)

configuration_cities_label.grid(
    row=0,
    column=3,
    padx=15
)


# ============================================================
# PoW results
# ============================================================

pow_results_frame = ttk.LabelFrame(
    results_frame,
    text="Proof of Work",
    padding=15
)

pow_results_frame.grid(
    row=2,
    column=0,
    sticky="nesw",
    padx=(0, 10),
    pady=(0, 20)
)


ttk.Label(
    pow_results_frame,
    text="Hash Rate"
).grid(
    row=0,
    column=0,
    sticky="w"
)


ttk.Label(
    pow_results_frame,
    text="X hashes/sec"
).grid(
    row=0,
    column=1,
    sticky="e",
    padx=20
)


ttk.Label(
    pow_results_frame,
    text="Average Hashes"
).grid(
    row=1,
    column=0,
    sticky="w"
)


average_hashes_label = ttk.Label(
    pow_results_frame,
    text=""
)

average_hashes_label.grid(
    row=1,
    column=1,
    sticky="e",
    padx=20
)


ttk.Label(
    pow_results_frame,
    text="Average Simulation Time"
).grid(
    row=2,
    column=0,
    sticky="w"
)


ttk.Label(
    pow_results_frame,
    text="XX.xx seconds"
).grid(
    row=2,
    column=1,
    sticky="e",
    padx=20
)


# ============================================================
# PoUW results
# ============================================================

pouw_results_frame = ttk.LabelFrame(
    results_frame,
    text="Proof of Useful Work",
    padding=15
)

pouw_results_frame.grid(
    row=2,
    column=1,
    sticky="nesw",
    padx=(10, 0),
    pady=(0, 20)
)


ttk.Label(
    pouw_results_frame,
    text="Computation Rate"
).grid(
    row=0,
    column=0,
    sticky="w"
)


ttk.Label(
    pouw_results_frame,
    text="X computations/sec"
).grid(
    row=0,
    column=1,
    sticky="e",
    padx=20
)


ttk.Label(
    pouw_results_frame,
    text="Average Computations"
).grid(
    row=1,
    column=0,
    sticky="w"
)


average_computations_label = ttk.Label(
    pouw_results_frame,
    text=""
)

average_computations_label.grid(
    row=1,
    column=1,
    sticky="e",
    padx=20
)


ttk.Label(
    pouw_results_frame,
    text="Average Simulation Time"
).grid(
    row=2,
    column=0,
    sticky="w"
)


ttk.Label(
    pouw_results_frame,
    text="XX.xx seconds"
).grid(
    row=2,
    column=1,
    sticky="e",
    padx=20
)


# ============================================================
# Comparison
# ============================================================

comparison_frame = ttk.LabelFrame(
    results_frame,
    text="Comparison",
    padding=15
)

comparison_frame.grid(
    row=3,
    column=0,
    columnspan=2,
    sticky="nesw",
    pady=(0, 20)
)


comparison_frame.columnconfigure(
    0,
    weight=1
)


# ============================================================
# Simulation details
# ============================================================

node_frame = ttk.LabelFrame(
    results_frame,
    text="Simulation Details",
    padding=15
)

node_frame.grid(
    row=4,
    column=0,
    columnspan=2,
    sticky="we",
    pady=(0, 20)
)


ttk.Label(
    node_frame,
    text="PoW Node Results"
).grid(
    row=0,
    column=0,
    columnspan=4,
    sticky="w",
    pady=(0, 10)
)


ttk.Label(
    node_frame,
    text="Node 1: X hashes/sec"
).grid(
    row=1,
    column=0,
    padx=10
)


ttk.Label(
    node_frame,
    text="Node 2: X hashes/sec"
).grid(
    row=1,
    column=1,
    padx=10
)


ttk.Label(
    node_frame,
    text="Node 3: X hashes/sec"
).grid(
    row=1,
    column=2,
    padx=10
)


ttk.Label(
    node_frame,
    text="Node 4: X hashes/sec"
).grid(
    row=1,
    column=3,
    padx=10
)