import os
import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot):
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
    valid_laps = sorted(df['Lap'].unique())[1:-1]
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

    def smooth(data, w):
        w = int(w)
        if w <= 1:
            return data
        return np.convolve(data, np.ones(w) / w, mode='same')

    def fastest_laps(lt, n=5):
        return [lap for lap, _ in sorted(lt.items(), key=lambda kv: kv[1])[:n]]

    # ── dropdown sources: label → (dataframe, [laps], average?) ──
    sources = {}
    for lap in valid_laps:
        sources[f"Lap {lap} — {laptimes[lap]:.2f}s"] = (df, [lap], False)
    sources["Top 5 Average"] = (df, fastest_laps(laptimes), True)
    if df2 is not None:
        for lap in sorted(laptimes2.keys()):
            sources[f"df2 Lap {lap} — {laptimes2[lap]:.2f}s"] = (df2, [lap], False)
        sources["df2 Top 5 Average"] = (df2, fastest_laps(laptimes2), True)

    def get_series(key, col):
        d, laps, avg = sources[key]
        if not avg:
            return d[d['Lap'] == laps[0]][col].to_numpy(float)
        # average across laps, resampling each to a common length by fraction of lap
        arrs = [d[d['Lap'] == lap][col].to_numpy(float) for lap in laps]
        length = int(np.median([len(a) for a in arrs]))
        xnew = np.linspace(0, 1, length)
        acc = np.zeros(length)
        for a in arrs:
            acc += np.interp(xnew, np.linspace(0, 1, len(a)), a)
        return acc / len(arrs)

    # channel key → (label, column, default colour, default on?, on secondary axis?)
    CHANNELS = (
        ('steer', "Steering",  'Steering',           COLOURS[0], True,  False),
        ('thr',   "Throttle",  'Throttle and brake', COLOURS[1], True,  False),
        ('yaw',   "Yaw rate",  'Gyro Yaw',           COLOURS[4], False, True),
        ('pitch', "Gyro Pitch", 'Gyro Pitch',         COLOURS[2], False, True),
        ('roll',  "Gyro Roll",  'Gyro Roll',          COLOURS[3], False, True),
    )

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
    navbtn("Comparison Run", lambda: show_load_df2(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Lap Times", lambda: show_laptime_chart(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_channel_plot))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot))
    navbtn("Custom Plot", lambda: show_channel_plot(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart))
    navbtn("Save Run", lambda: show_save_run(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_laptime_chart, show_channel_plot))

    container = tk.Frame(outer)
    container.pack(fill="both", expand=True)

    # ── one control panel per trace ──────────────────────────
    def build_panel(parent, title, default_key):
        frame = tk.Frame(parent, bd=1, relief="groove")
        tk.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(pady=5)

        lap_var = tk.StringVar(value=default_key)
        ttk.Combobox(frame, textvariable=lap_var, values=list(sources.keys()),
                     state="readonly", width=22).pack(pady=5)

        c = {'lap_var': lap_var}

        for name, label, _col_name, default_col, default_on, _sec in CHANNELS:
            block = tk.LabelFrame(frame, text=label)
            block.pack(padx=8, pady=2, fill="x")

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
                             orient="horizontal", label="Thickness", width=10,
                             command=lambda v: draw())
            width.set(1); width.pack(fill="x")

            sm = tk.Scale(block, from_=1, to=101, resolution=2,
                          orient="horizontal", label="Smoothing", width=10,
                          command=lambda v: draw())
            sm.set(1); sm.pack(fill="x")

            c[name] = {'on': on, 'col': col, 'w': width, 'sm': sm}

        return frame, c

    # defaults: main top-5 vs df2 top-5 (if a comparison run is loaded)
    left_default = "Top 5 Average"
    right_default = "df2 Top 5 Average" if df2 is not None else list(sources.keys())[0]

    left_frame, left = build_panel(container, "Trace 1", left_default)
    left_frame.pack(side="left", fill="y", padx=10)

    right_frame, right = build_panel(container, "Trace 2", right_default)
    right_frame.pack(side="right", fill="y", padx=10)

    # distinct colours so the two traces don't clash
    right['steer']['col'].set(COLOURS[2])
    right['thr']['col'].set(COLOURS[3])
    right['yaw']['col'].set(COLOURS[5])

    # ── figure in the middle (with zoom toolbar) ─────────────
    graph_frame = tk.Frame(container)
    graph_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fig = Figure(figsize=(9, 5), dpi=100)
    ax = fig.add_subplot(111)          # left axis: steering / throttle (µs)
    ax2 = ax.twinx()                   # right axis: yaw rate (deg/s)
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    # zoom / pan / reset toolbar
    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")

    def draw():
        # remember current zoom so a redraw (slider move etc.) doesn't reset it
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        had_data = ax.has_data()

        ax.clear()
        ax2.clear()

        for ctrl, tag in ((left, "T1"), (right, "T2")):
            key = ctrl['lap_var'].get()
            if key not in sources:
                continue

            for name, label, col_name, _dc, _do, secondary in CHANNELS:
                if not ctrl[name]['on'].get():
                    continue
                y = smooth(get_series(key, col_name), ctrl[name]['sm'].get())
                x = np.arange(len(y)) * 0.01
                target = ax2 if secondary else ax
                target.plot(x, y, color=ctrl[name]['col'].get(),
                            linewidth=ctrl[name]['w'].get(),
                            linestyle="-",
                            label=f"{tag} {label}")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Steering / Throttle (µs)")
        ax2.set_ylabel("Yaw rate (deg/s)")
        ax.grid(alpha=0.3)

        # one combined legend across both axes
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        if h1 or h2:
            ax.legend(h1 + h2, l1 + l2, loc="upper right")

        # restore the zoom the user had, unless this is the very first draw
        if had_data:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        canvas.draw()

    for ctrl in (left, right):
        ctrl['lap_var'].trace_add("write", lambda *_: draw())

    draw()