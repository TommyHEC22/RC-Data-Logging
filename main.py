import tkinter as tk
from macsafe import make_navbtn, force_light_mode
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
from trim import show_prep_data

root = tk.Tk()
force_light_mode(root)
root.state("zoomed")
root.title("Race Engineer")

df = None

# ── run comments ────────────────────────────────────────────────────────────
# A saved run can carry a comment as "# ..." header lines at the top of the CSV
# (see saverun.py). We stash the loaded run's comment next to its data so the
# Analysis page can show it: comment_main.txt for the main run, comment.txt for
# the comparison run (comment.txt is also written by the Comparison Run page).
MAIN_COMMENT_FILE = "comment_main.txt"
DF2_COMMENT_FILE = "comment.txt"


def read_run_comment(csv_path):
    """Return the leading '# ...' comment block of a CSV as plain text ('' if none)."""
    lines = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#"):
                    lines.append(stripped[1:].strip())
                else:
                    break
    except Exception as e:
        print("Error reading comment:", e)
    return "\n".join(lines).strip()


def write_comment(path, text):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text or "")
    except Exception as e:
        print("Error writing", path, ":", e)


def carry_comment(src, dst):
    """When the current run is pushed into the df2 slot, move its comment too."""
    try:
        with open(src, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        text = ""
    write_comment(dst, text)



def build_navbar(parent):
    navbar = tk.Frame(parent, bg="#1e1e1e", height=52)
    navbar.pack(side="top", fill="x")
    navbar.pack_propagate(False)          # keep the 52px height

    def navbtn(text, cmd):
        make_navbtn(navbar, text, cmd)

    # only navigate once data is actually loaded (inert on the loader screen)
    def nav(page, *siblings):
        if df is not None:
            page(root, df, *siblings)

    navbtn("Load Data", show_loader)
    #navbtn("Prep Data, lambda": nav(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Comparison Run", lambda: nav(show_load_df2, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart, show_prep_data))
    navbtn("Analysis", lambda: nav(show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart, show_prep_data))
    navbtn("Lap Times", lambda: nav(show_laptime_chart, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_prep_data))
    navbtn("Steering & Throttle", lambda: nav(show_steeringthrottle_graph, show_analysis, show_friction_circle, show_gforces, show_histograms, show_laptime_chart, show_prep_data))
    navbtn("Friction Circle", lambda: nav(show_friction_circle, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_laptime_chart, show_prep_data))
    navbtn("G-Forces", lambda: nav(show_gforces, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_laptime_chart, show_prep_data))
    navbtn("Histograms", lambda: nav(show_histograms, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_laptime_chart, show_prep_data))
    navbtn("Custom Plot", lambda: nav(show_channel_plot, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_laptime_chart, show_prep_data))
    navbtn("Save Run", lambda: nav(show_save_run, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart, show_prep_data))

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
        df.to_csv("df2.csv", index=False)
        carry_comment(MAIN_COMMENT_FILE, DF2_COMMENT_FILE)   # old run -> comparison slot
    except Exception as e:
        print("Df doesnt exist...", e)
    try:
        file = easygui.fileopenbox()
        if not file:
            return
        write_comment(MAIN_COMMENT_FILE, read_run_comment(file))   # capture this run's comment
        df = pd.read_csv(file, comment="#")
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data)
    except Exception as e:
        print("Error loading file:", e)


def load_new_data():
    global df
    try:
        df.to_csv("df2.csv", index=False)
        carry_comment(MAIN_COMMENT_FILE, DF2_COMMENT_FILE)   # old run -> comparison slot
    except Exception as e:
        print("Df doesnt exist...", e)
    try:
        file = easygui.fileopenbox()
        if not file:
            return
        write_comment(MAIN_COMMENT_FILE, "")   # a freshly parsed .clf run has no comment
        df = pd.read_csv(convert_file_to_csv(file))
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data)
    except Exception as e:
        print("Error loading file:", e)


show_loader()
root.mainloop()