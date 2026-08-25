import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("PoW vs PoUW Simulation")
#root.geometry("800x600")

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



run_button = ttk.Button(settings_frame, text="Run")
run_button.grid(row=3, column=0, columnspan=2, pady=(10, 20))

root.mainloop()