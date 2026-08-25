import tkinter as tk
from tkinter import ttk
from mainFunctions import MainFunctions
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def run_settings():

    num_of_nodes = nodes.get()
    num_of_runs = runs.get()
    num_of_cities = cities.get()
    block_hash_difficulty = difficulty.get()

    simulation = MainFunctions(
    num_of_nodes,
    num_of_cities, 
    num_of_runs,
    block_hash_difficulty
    )

    average_hashes, average_computations = simulation.run_simulation()

    average_hashes_label.config(text= f"{average_hashes:,.2f}")
    average_computations_label.config(text= f"{average_computations:,.2f}")

    show_comparison_graph(average_hashes, average_computations)

    settings_frame.grid_remove()
    results_frame.grid()

def show_comparison_graph(average_hashes, average_computations):

    figure = Figure(figsize=(5, 3), dpi=100)

    ax = figure.add_subplot(111)

    methods = ["PoW", "PoUW"]
    values = average_hashes, average_computations

    ax.bar(methods, values)

    ax.set_title("Average Computational Work")
    ax.set_ylabel("Computational Work")

    figure.tight_layout()

    canvas = FigureCanvasTkAgg(figure, master=comparison_frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky="nesw")

root = tk.Tk()
root.title("PoW vs PoUW Simulation")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)



settings_frame = ttk.Frame(root, padding=20)
settings_frame.grid(column=0, row=0, sticky=("wnes"))

settings_frame.columnconfigure(0, weight=1)
settings_frame.columnconfigure(1, weight=1)

title = ttk.Label(settings_frame, text="PoW vs PouW Benchmark")
title.grid(row=0, column=0, columnspan=2, pady=(0, 20))



benchmark_frame = ttk.LabelFrame(settings_frame, text="Benchmark settings", padding=15)
benchmark_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 20))

benchmark_frame.columnconfigure(1, weight=1)

ttk.Label(
    benchmark_frame,
    text="Number of Nodes"
).grid(row=0, column=0, sticky="w", padx=5, pady=10)

nodes_frame = ttk.Frame(benchmark_frame)

nodes_frame.grid(row=0, column=1, sticky="w", padx=10)

# Just a placeholder
nodes = tk.IntVar(value=4)

ttk.Radiobutton(
    nodes_frame,
    text="3",
    variable=nodes,
    value=3
).grid(row=0, column=0, padx=15)

ttk.Radiobutton(
    nodes_frame,
    text="4",
    variable=nodes,
    value=4
).grid(row=0, column=1, padx=15)

ttk.Radiobutton(
    nodes_frame,
    text="5",
    variable=nodes,
    value=5
).grid(row=0, column=2, padx=15)


ttk.Label(
    benchmark_frame,
    text="Number of Runs"
).grid(row=1, column=0, sticky="w", padx=5, pady=10)

runs_frame = ttk.Frame(benchmark_frame)
runs_frame.grid(row=1, column=1, sticky="w", padx=10)

# Also a placeholder
runs = tk.IntVar(value=10)

ttk.Radiobutton(
    runs_frame,
    text="5",
    variable=runs,
    value=5
).grid(row=0, column=0, padx=15)

ttk.Radiobutton(
    runs_frame,
    text="10",
    variable=runs,
    value=10
).grid(row=0, column=1, padx=15)

ttk.Radiobutton(
    runs_frame,
    text="20",
    variable=runs,
    value=20
).grid(row=0, column=2, padx=15)



pow_frame = ttk.LabelFrame(settings_frame, text="PoW Settings")
pow_frame.grid(row=2, column=0, sticky="nesw", padx=(0, 10), pady=(0, 20))

pow_frame.columnconfigure(1, weight=1)

ttk.Label(
    pow_frame, 
    text="Difficulty"
).grid(row=0, column=0, sticky="w", padx=5, pady=10)

difficulty_frame = ttk.Frame(pow_frame)
difficulty_frame.grid(row=0, column=1, sticky="w", padx=10)

# Another placeholder
difficulty = tk.IntVar(value=4)

ttk.Radiobutton(
    difficulty_frame,
    text="Low",
    variable=difficulty,
    value=2
).grid(row=0, column=0, padx=15)

ttk.Radiobutton(
    difficulty_frame,
    text="Medium",
    variable=difficulty,
    value=4
).grid(row=0, column=1, padx=15)

ttk.Radiobutton(
    difficulty_frame,
    text="High",
    variable=difficulty,
    value=6
).grid(row=0, column=2, padx=15)



pouw_frame = ttk.LabelFrame(settings_frame, text="PoUW Settings", padding=15)
pouw_frame.grid(row=2, column=1, sticky="nesw", padx=(10, 0), pady=(0, 20))

pouw_frame.columnconfigure(1, weight=1)

ttk.Label(
    pouw_frame,
    text="Number of Cities",
    width=18
).grid(row=0, column=0, sticky="w", padx=5, pady=10)

cities_frame = ttk.Frame(pouw_frame)
cities_frame.grid(row=0, column=1, sticky="w", padx=10)

# Same placeholder
cities = tk.IntVar(value=9)

ttk.Radiobutton(
    cities_frame,
    text="7",
    variable=cities,
    value=7
).grid(row=0, column=0, padx=15)

ttk.Radiobutton(
    cities_frame,
    text="9",
    variable=cities,
    value=9
).grid(row=0, column=1, padx=15)

ttk.Radiobutton(
    cities_frame,
    text="11",
    variable=cities,
    value=11
).grid(row=0, column=2, padx=15)

ttk.Label(
    pouw_frame,
    text="Verification",
    width=18
).grid(
    row=1,
    column=0,
    sticky="w",
    padx=5,
    pady=10
)

verification_frame = ttk.Frame(pouw_frame)
verification_frame.grid(row=1, column=1, sticky="w", padx=10)

# Same thing
verification = tk.StringVar(value="none")

ttk.Radiobutton(
    verification_frame,
    text="None",
    variable=verification,
    value="none"
).grid(row=0, column=0, padx=15)

ttk.Radiobutton(
    verification_frame,
    text="Easy",
    variable=verification,
    value="easy"
).grid(row=0, column=1, padx=15)

ttk.Radiobutton(
    verification_frame,
    text="Normal",
    variable=verification,
    value="normal"
).grid(row=0, column=2, padx=15)



run_button = ttk.Button(settings_frame, text="Run", command=run_settings)
run_button.grid(row=3, column=0, columnspan=2, pady=(10, 20))



results_frame = ttk.Frame(root, padding=20)
results_frame.grid(row=0, column=0, sticky="nesw")

results_frame.grid_remove()

results_frame.columnconfigure(0, weight=1)
results_frame.columnconfigure(1, weight=1)

ttk.Label(
    results_frame,
    text="Simulation Results",
).grid(row=0, column=0, columnspan=2, pady=(0, 20))



configuration_frame = ttk.LabelFrame(results_frame, text="Configuration", padding=15)
configuration_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 20))

ttk.Label(
    configuration_frame,
    text= f"Nodes: {nodes.get()}"
).grid(row=0, column=0, padx=15)

ttk.Label(
    configuration_frame,
    text= f"Runs: {runs.get()}"
).grid(row=0, column=1, padx=15)

ttk.Label(
    configuration_frame,
    text= f"PoW Difficulty: {difficulty.get()}"
).grid(row=0, column=2, padx=15)

ttk.Label(
    configuration_frame,
    text= f"Cities: {cities.get()}"
).grid(row=0, column=3, padx=15)




pow_frame = ttk.LabelFrame(results_frame, text="Proof of Work", padding=15)
pow_frame.grid(row=2, column=0, sticky="nesw", padx=(0, 10), pady=(0, 20))

ttk.Label(
    pow_frame,
    text="Hash Rate"
).grid(row=0, column=0, sticky="w")

ttk.Label(
    pow_frame,
    text="X hashes/sec"
).grid(row=0, column=1, sticky="e", padx=20)

ttk.Label(
    pow_frame,
    text="Average Hashes"
).grid(row=1, column=0, sticky="w")

average_hashes_label = ttk.Label(pow_frame, text= "")
average_hashes_label.grid(row=1, column=1, sticky="e", padx=20)

ttk.Label(
    pow_frame,
    text="Average Simulation Time"
).grid(row=2, column=0, sticky="w")

ttk.Label(
    pow_frame,
    text="XX.xx seconds"
).grid(row=2, column=1, sticky="e", padx=20)



pouw_frame = ttk.LabelFrame(results_frame, text="Proof of Useful Work")
pouw_frame.grid(row=2, column=1, sticky="nesw", padx=(10, 0), pady=(0, 20))

ttk.Label(
    pouw_frame,
    text="Computation Rate"
).grid(row=0, column=0, sticky="w")

ttk.Label(
    pouw_frame,
    text="X computations/sec"
).grid(row=0, column=1, sticky="e", padx=20)

ttk.Label(
    pouw_frame,
    text="Average Computations"
).grid(row=1, column=0, sticky="w")

average_computations_label = ttk.Label(pouw_frame, text="")
average_computations_label.grid(row=1, column=1, sticky="e", padx=20)

ttk.Label(
    pouw_frame,
    text="Average Simulation Time"
).grid(row=2, column=0, sticky="w")

ttk.Label(
    pouw_frame,
    text="XX.xx seconds"
).grid(row=2, column=1, sticky="e", padx=20)



comparison_frame = ttk.LabelFrame(results_frame, text="Comparison", padding=15)
comparison_frame.grid(row=3, column=0, columnspan=2, sticky="nesw", pady=(0, 20))

comparison_frame.columnconfigure(0, weight=1)
comparison_frame.rowconfigure(0, weight=1)

# Placeholder for graph
#ttk.Label(
#    comparison_frame,
#    text="Graph will go here"
#).grid(row=0, column=0, padx=20, pady=40)



node_frame = ttk.LabelFrame(results_frame, text="Simulation Details", padding=15)
node_frame.grid(row=4, column=0, columnspan=2, sticky=("we"), pady=(0, 20))

ttk.Label(
    node_frame,
    text="PoW Node Results"
).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))

ttk.Label(
    node_frame, 
    text="Node 1: X hashes/sec"
    ).grid(row=1, column=0, padx=10)


ttk.Label(
    node_frame, 
    text="Node 2: X hashes/sec"
    ).grid(row=1, column=1, padx=10)


ttk.Label(
    node_frame, 
    text="Node 3: X hashes/sec"
    ).grid(row=1, column=2, padx=10)


ttk.Label(
    node_frame, 
    text="Node 4: X hashes/sec"
    ).grid(row=1, column=3, padx=10)

root.update_idletasks()


width = root.winfo_reqwidth()
height = root.winfo_reqheight()

x = (root.winfo_screenwidth() - width) // 2
y = (root.winfo_screenheight() - height) // 2

root.geometry(f"{width}x{height}+{x}+{y}")

root.mainloop()