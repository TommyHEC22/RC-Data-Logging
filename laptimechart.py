import os
import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def show_laptime_chart(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run):
    root.state("zoomed")
    for w in root.winfo_children():
        w.destroy()

    # ── lap times ────────────────────────────────────────────
    def get_laptimes_dictionary(d):
        laps = d.groupby('Lap')
        laptimes = {}
        for lap in laps:
            lap_num = lap[0]
            end = lap[1].iloc[-1]['Time']
            start = lap[1].iloc[0]['Time']
            laptimes[lap_num] = float(end - start)
        del laptimes[min(laptimes.keys())]
        del laptimes[max(laptimes.keys())]
        return laptimes

    df['Time'] = df.groupby('Lap').cumcount() * 0.01
    laptimes = get_laptimes_dictionary(df)

    # comparison run, if one has been staged as df2.csv
    df2 = None
    laptimes2 = {}
    if os.path.exists("df2.csv"):
        try:
            df2 = pd.read_csv("df2.csv")
            df2['Time'] = df2.groupby('Lap').cumcount() * 0.01
            laptimes2 = get_laptimes_dictionary(df2)
        except Exception as e:
            print("Could not use df2.csv:", e)
            df2 = None

    COLOURS = ["#002AFF", "#D93A00", '#2E8B00', "#CA004A", "#600076", '#000000']

    # ── dropdown sources: label → (laptimes dict, good-laps-only?) ──
    sources = {
        "All laps":  (laptimes, False),
        "Good laps": (laptimes, True),
    }
    if df2 is not None:
        sources["df2 All laps"]  = (laptimes2, False)
        sources["df2 Good laps"] = (laptimes2, True)

    def series_for(key):
        lt, good = sources[key]
        items = sorted(lt.items())               # by lap number
        if good and lt:
            best = min(lt.values())
            items = [(l, t) for l, t in items if t <= best + 1.0]   # drop >1s off best
        return [l for l, _ in items], [t for _, t in items]

    outer = tk.Frame(root)
    outer.pack(fill="both", expand=True)

    # ── top nav bar ──────────────────────────────────────
    navbar = tk.Frame(outer, bg="#1e1e1e", height=52)
    navbar.pack(side="top", fill="x")
    navbar.pack_propagate(False)

    def navbtn(text, cmd):
        tk.Button(navbar, text=text, command=cmd,
                  bg="#2d2d2d", fg="white",
                  activebackground="#3d3d3d", activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 11),
                  padx=18, pady=6, cursor="hand2"
                  ).pack(side="left", padx=(12, 0), pady=8)

    navbtn("Load Data", lambda: show_loader())
    navbtn("Comparison Run", lambda: show_load_df2(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart))
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("Lap Times", lambda: show_laptime_chart(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("Save Run", lambda: show_save_run(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart))

    container = tk.Frame(outer)
    container.pack(fill="both", expand=True)

    # ── control panel (left) ─────────────────────────────
    def build_panel(parent, title, default_key, default_col, default_on):
        frame = tk.Frame(parent, bd=1, relief="groove")
        tk.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(pady=5)

        lap_var = tk.StringVar(value=default_key)
        ttk.Combobox(frame, textvariable=lap_var, values=list(sources.keys()),
                     state="readonly", width=18).pack(pady=5)

        on = tk.BooleanVar(value=default_on)
        tk.Checkbutton(frame, text="Show", variable=on,
                       command=lambda: draw()).pack(anchor="w", padx=8)

        col = tk.StringVar(value=default_col)
        swatch_row = tk.Frame(frame)
        swatch_row.pack(pady=4)
        for hexcol in COLOURS:
            tk.Button(swatch_row, bg=hexcol, width=2, height=1,
                      relief="flat", bd=1,
                      command=lambda h=hexcol, cv=col: (cv.set(h), draw())
                      ).pack(side="left", padx=1)

        return frame, {'lap_var': lap_var, 'on': on, 'col': col}

    controls = tk.Frame(container)
    controls.pack(side="left", fill="y", padx=10, pady=10)

    left_default = "All laps"
    right_default = "df2 All laps" if df2 is not None else "Good laps"

    left_frame, left = build_panel(controls, "Trace 1", left_default, COLOURS[0], True)
    left_frame.pack(fill="x", pady=(0, 10))

    right_frame, right = build_panel(controls, "Trace 2", right_default, COLOURS[1], True)
    right_frame.pack(fill="x")

    # ── figure (middle) ──────────────────────────────────
    graph_frame = tk.Frame(container)
    graph_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fig = Figure(figsize=(9, 5), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")

    def draw():
        ax.clear()

        any_line = False
        for ctrl in (left, right):
            if not ctrl['on'].get():
                continue
            laps, times = series_for(ctrl['lap_var'].get())
            if not laps:
                continue
            ax.plot(laps, times, marker='o', linewidth=1.5,
                    color=ctrl['col'].get(), label=ctrl['lap_var'].get())
            if len(laps) >= 2:
                m, b = np.polyfit(laps, times, 1)
                ax.plot(laps, [m * l + b for l in laps],
                        color="#888888", linewidth=2, alpha=0.5, zorder=1)
            any_line = True

        ax.set_xlabel("Lap number")
        ax.set_ylabel("Lap time (s)")
        ax.grid(alpha=0.3)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))   # whole lap numbers
        if any_line:
            ax.legend(loc="upper right")

        fig.tight_layout()
        canvas.draw()

    for ctrl in (left, right):
        ctrl['lap_var'].trace_add("write", lambda *_: draw())

    draw()