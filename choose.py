import os
import tkinter as tk
from macsafe import make_navbtn, force_light_mode
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from analysis import compute_laptimes


def show_channel_plot(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_prep_data):
    root.state("zoomed")
    for w in root.winfo_children():
        w.destroy()

    # ── lap times ────────────────────────────────────────────
    valid_laps = sorted(df['Lap'].unique())[1:-1]
    laptimes = compute_laptimes(df)

    # comparison run, if a df2.csv is present
    df2 = None
    if os.path.exists("df2.csv"):
        try:
            df2 = pd.read_csv("df2.csv")
            valid_laps2 = sorted(df2['Lap'].unique())[1:-1]
            laptimes2 = compute_laptimes(df2)
        except Exception as e:
            print("Could not use df2.csv:", e)
            df2 = None

    COLOURS = ["#002AFF", "#D93A00", '#2E8B00', "#CA004A", "#600076", '#000000']

    def smooth(data, w):
        w = int(w)
        if w <= 1:
            return data
        return np.convolve(data, np.ones(w) / w, mode='same')

    def fastest_laps(lt, n=5):
        return [lap for lap, _ in sorted(lt.items(), key=lambda kv: kv[1])[:n]]

    # ── dropdown sources: label → (dataframe, [laps], average?) ──
    sources = {}
    for l in valid_laps:
        sources[f"Lap {l} — {laptimes[l]:.2f}s"] = (df, [l], False)
    sources["Top 5 Average"] = (df, fastest_laps(laptimes), True)
    if df2 is not None:
        for l in valid_laps2:
            sources[f"df2 Lap {l} — {laptimes2[l]:.2f}s"] = (df2, [l], False)
        sources["df2 Top 5 Average"] = (df2, fastest_laps(laptimes2), True)

    lap_labels = sources          # kept name so the panels read the same

    # parameters the user can choose for each slot
    PARAMETERS = [
        'Timestamp',
        'Lap',
        'Laptrig status', 'Laptrig width', 'Laptrig period',
        'Speed all', 'Distance',
        'Date and time',
        'Speed motor', 'Speed RL', 'Speed RR',
        'RPM',
        'Temp sensor',
        'Steering', 'Throttle and brake',
        'Steering width', 'Throttle and brake width',
        'Acceleration X', 'Acceleration Y', 'Acceleration Z',
        'Gyro Roll', 'Gyro Pitch', 'Gyro Yaw',
        'Beacon',
        'Speed motor raw value', 'Speed RL raw value', 'Speed RR raw value',
        'Speed motor duty cycle', 'Speed RL duty cycle', 'Speed RR duty cycle',
    ]

    # three choosable slots per panel; defaults picked from the parameter list
    SLOTS = (
        ('s1', 'Steering',           COLOURS[0], True),
        ('s2', 'Throttle and brake', COLOURS[1], True),
        ('s3', 'Gyro Yaw',           COLOURS[4], False),
    )

    def series_for(key, param):
        d, laps, avg = sources[key]
        if not avg:
            lap_df = d[d['Lap'] == laps[0]].reset_index(drop=True)
            return lap_df[param].to_numpy(float)
        # average across laps, resampling each to a common length by fraction of lap
        arrs = [d[d['Lap'] == lap].reset_index(drop=True)[param].to_numpy(float)
                for lap in laps]
        length = int(np.median([len(a) for a in arrs]))
        xnew = np.linspace(0, 1, length)
        acc = np.zeros(length)
        for a in arrs:
            acc += np.interp(xnew, np.linspace(0, 1, len(a)), a)
        return acc / len(arrs)

    outer = tk.Frame(root)
    outer.pack(fill="both", expand=True)

    # ── top nav bar ──────────────────────────────────────
    navbar = tk.Frame(outer, bg="#1e1e1e", height=52)
    navbar.pack(side="top", fill="x")
    navbar.pack_propagate(False)

    def navbtn(text, cmd):
        make_navbtn(navbar, text, cmd)

    navbtn("Load Data", lambda: show_loader())
    navbtn("Prep Data", lambda: show_prep_data(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Comparison Run", lambda: show_load_df2(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Lap Times", lambda: show_laptime_chart(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_channel_plot, show_prep_data))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data))
    navbtn("Custom Plot", lambda: show_channel_plot(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_prep_data))
    navbtn("Save Run", lambda: show_save_run(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart, show_channel_plot, show_prep_data))

    container = tk.Frame(outer)
    container.pack(fill="both", expand=True)

    # ── one control panel per lap ────────────────────────────
    def build_panel(parent, title):
        frame = tk.Frame(parent, bd=1, relief="groove")
        tk.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(pady=5)

        lap_var = tk.StringVar(value=list(lap_labels)[0])
        ttk.Combobox(frame, textvariable=lap_var, values=list(lap_labels.keys()),
                     state="readonly", width=16).pack(pady=5)

        c = {'lap_var': lap_var}

        for name, default_param, default_col, default_on in SLOTS:
            block = tk.LabelFrame(frame, text="Parameter")
            block.pack(padx=8, pady=5, fill="x")

            # parameter chooser
            param = tk.StringVar(value=default_param)
            ttk.Combobox(block, textvariable=param, values=PARAMETERS,
                         state="readonly", width=20).pack(pady=2)

            on = tk.BooleanVar(value=default_on)
            tk.Checkbutton(block, text="Show", variable=on,
                           command=lambda: draw()).pack(anchor="w")

            # colour swatch row
            col = tk.StringVar(value=default_col)
            swatch_row = tk.Frame(block)
            swatch_row.pack(pady=2)
            for hexcol in COLOURS:
                tk.Button(swatch_row, bg=hexcol, width=2, height=1,
                          relief="flat", bd=1,
                          command=lambda h=hexcol, cv=col: (cv.set(h), draw())
                          ).pack(side="left", padx=1)

            width = tk.Scale(block, from_=0.5, to=6, resolution=0.5,
                             orient="horizontal", label="Thickness",
                             command=lambda v: draw())
            width.set(1); width.pack(fill="x")

            sm = tk.Scale(block, from_=1, to=101, resolution=2,
                          orient="horizontal", label="Smoothing",
                          command=lambda v: draw())
            sm.set(15); sm.pack(fill="x")

            amp = tk.Scale(block, from_=0.1, to=25, resolution=0.5,
               orient="horizontal", label="Line Amplification",
               command=lambda v: draw())
            amp.set(1.0)
            amp.pack(fill="x")

            c[name] = {'param': param, 'on': on, 'col': col, 'w': width, 'sm': sm, 'amp': amp}
            param.trace_add("write", lambda *_: draw())

        return frame, c

    left_frame, left = build_panel(container, "Lap 1")
    left_frame.pack(side="left", fill="y", padx=10)

    right_frame, right = build_panel(container, "Lap 2")
    right_frame.pack(side="right", fill="y", padx=10)

    # Lap 2 starts hidden so the plot isn't cluttered; toggle on to compare.
    # Laps are told apart by line style (Lap 1 solid, Lap 2 dashed).
    for name, *_ in SLOTS:
        right[name]['on'].set(False)

    # ── figure in the middle (with zoom toolbar) ─────────────
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
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        had_data = ax.has_data()

        ax.clear()

        any_line = False
        for ctrl, tag, ls in ((left, "L1", "-"), (right, "L2", "--")):
            key = ctrl['lap_var'].get()
            if key not in sources:
                continue

            for name, *_ in SLOTS:
                slot = ctrl[name]
                if not slot['on'].get():
                    continue
                param = slot['param'].get()
                y = smooth(series_for(key, param), slot['sm'].get())
                # Amplify line vertically around zero
                y = y * slot['amp'].get()
                x = np.arange(len(y)) * 0.01
                ax.plot(x, y,
                        color=slot['col'].get(),
                        linewidth=slot['w'].get(),
                        linestyle=ls,
                        label=f"{tag} {param}")
                any_line = True

        ax.axhline(0, color="#cccccc", lw=0.8, zorder=0)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Value")
        if any_line:
            ax.legend(loc="upper right", fontsize=8)
        ax.grid(alpha=0.3)

        if had_data:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        canvas.draw()

    for ctrl in (left, right):
        ctrl['lap_var'].trace_add("write", lambda *_: draw())

    draw()