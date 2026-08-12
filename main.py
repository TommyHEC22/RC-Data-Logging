import tkinter as tk
from tkinter import ttk
from V2_parser import convert_file_to_csv
import easygui
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from analysis import show_analysis
from steerthrottlegraph import show_steeringthrottle_graph

root = tk.Tk()
root.state("zoomed")
root.title("Race Engineer")

df = None

button = tk.Button(
    root,
    bg="#2d2d2d", fg="white",
    activebackground="#3d3d3d", activeforeground="white",
    relief="flat", bd=0,
    font=("Segoe UI", 11)
)

def show_loader():
    for w in root.winfo_children():
        w.destroy()
    tk.Label(root, text="Load a .clf file to analyze", font=("Segoe UI", 30)).pack(pady=(100, 10))
    ttk.Button(root, text="Load .clf Data", command=load_new_data).pack(pady=20, ipadx=20, ipady=20)
    ttk.Button(root, text="QuickLoad .csv Data", command=quickload_old_data).pack(pady=20, ipadx=20, ipady=20)

def quickload_old_data():
    global df
    try:
        file = easygui.fileopenbox()
        df = pd.read_csv(file)
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis(root, df, show_steeringthrottle_graph)          # swap to the next screen
    except Exception as e:
        print("Error loading file:", e)

def load_new_data():
    global df
    try:
        file = easygui.fileopenbox()
        df = pd.read_csv(convert_file_to_csv(file))
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis(root, df, show_steeringthrottle_graph)          # swap to the next screen
    except Exception as e:
        print("Error loading file:", e)


show_loader()
root.mainloop()