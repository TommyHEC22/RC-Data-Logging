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
from frictioncircle import show_friction_circle
from gforce import show_gforces
from histograms import show_histograms
from comparedata import show_load_df2
from saverun import show_save_run
from laptimechart import show_laptime_chart
from choose import show_channel_plot

root = tk.Tk()
root.state("zoomed")
root.title("Race Engineer")

df = None


def build_navbar(parent):
    navbar = tk.Frame(parent, bg="#1e1e1e", height=52)
    navbar.pack(side="top", fill="x")
    navbar.pack_propagate(False)          # keep the 52px height

    def navbtn(text, cmd):
        tk.Button(navbar, text=text, command=cmd,
                  bg="#2d2d2d", fg="white",
                  activebackground="#3d3d3d", activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 11),
                  padx=18, pady=6, cursor="hand2"
                  ).pack(side="left", padx=(12, 0), pady=8)

    # only navigate once data is actually loaded (inert on the loader screen)
    def nav(page, *siblings):
        if df is not None:
            page(root, df, *siblings)

    navbtn("Load Data", show_loader)
    navbtn("Comparison Run", lambda: nav(show_load_df2, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart))
    navbtn("Analysis", lambda: nav(show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart))
    navbtn("Lap Times", lambda: nav(show_laptime_chart, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run))
    navbtn("Steering & Throttle", lambda: nav(show_steeringthrottle_graph, show_analysis, show_friction_circle, show_gforces, show_histograms, show_laptime_chart))
    navbtn("Friction Circle", lambda: nav(show_friction_circle, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_laptime_chart))
    navbtn("G-Forces", lambda: nav(show_gforces, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_laptime_chart))
    navbtn("Histograms", lambda: nav(show_histograms, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_laptime_chart))
    navbtn("Custom Plot", lambda: nav(show_channel_plot, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_laptime_chart))
    navbtn("Save Run", lambda: nav(show_save_run, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart))

    return navbar


def show_loader():
    for w in root.winfo_children():
        w.destroy()

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    build_navbar(container)

    body = tk.Frame(container)
    body.pack(side="top", fill="both", expand=True)

    inner = tk.Frame(body)
    inner.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(inner, text="Load a .clf file to analyze",
             font=("Segoe UI", 28, "bold")).pack(pady=(0, 30))

    def loadbtn(text, cmd):
        return tk.Button(inner, text=text, command=cmd,
                         bg="White", fg="Black",
                         activebackground="#dcdcdc", activeforeground="white",
                         relief="flat", bd=0, font=("Segoe UI", 12),
                         padx=30, pady=14, cursor="hand2")

    loadbtn("Load .clf Data", load_new_data).pack(pady=8)
    loadbtn("QuickLoad .csv Data", quickload_old_data).pack(pady=8)


def quickload_old_data():
    global df
    try:
        file = easygui.fileopenbox()
        df = pd.read_csv(file)
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot)
    except Exception as e:
        print("Error loading file:", e)


def load_new_data():
    global df
    try:
        file = easygui.fileopenbox()
        df = pd.read_csv(convert_file_to_csv(file))
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot)
    except Exception as e:
        print("Error loading file:", e)


show_loader()
root.mainloop()