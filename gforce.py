import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms):
    for w in root.winfo_children():
        w.destroy()

    # ── lap times ────────────────────────────────────────────
    valid_laps = sorted(df['Lap'].unique())[1:-1]

    def get_laptimes_dictionary(df):
        laps = df.groupby('Lap')
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
    lap_labels = {f"Lap {l} — {laptimes[l]:.2f}s": l for l in valid_laps}

    COLOURS = ["#002AFF", "#D93A00", '#2E8B00', "#CA004A", "#600076", '#000000']

    def smooth(data, w):
        w = int(w)
        if w <= 1:
            return data
        return np.convolve(data, np.ones(w) / w, mode='same')

    # channel key → (label, default colour, default on?)
    CHANNELS = (
        ('long',  "Longitudinal (X)", COLOURS[0], True),
        ('lat',   "Lateral (Y)",      COLOURS[1], True),
        ('vert',  "Vertical (Z)",     COLOURS[2], False),
        ('total', "Total (X+Y)",      COLOURS[5], True),
    )

    def channel_data(lap_df, key):
        ax_ = lap_df['Acceleration X'].to_numpy(float)
        ay_ = lap_df['Acceleration Y'].to_numpy(float)
        az_ = lap_df['Acceleration Z'].to_numpy(float)
        if key == 'long':  return ax_
        if key == 'lat':   return ay_
        if key == 'vert':  return az_
        return np.sqrt(ax_ ** 2 + ay_ ** 2)      # total = combined horizontal g

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

    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces))

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

        for name, label, default_col, default_on in CHANNELS:
            block = tk.LabelFrame(frame, text=label)
            block.pack(padx=8, pady=5, fill="x")

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

            c[name] = {'on': on, 'col': col, 'w': width, 'sm': sm}

        return frame, c

    left_frame, left = build_panel(container, "Lap 1")
    left_frame.pack(side="left", fill="y", padx=10)

    right_frame, right = build_panel(container, "Lap 2")
    right_frame.pack(side="right", fill="y", padx=10)

    # Lap 2 starts hidden so the plot isn't cluttered; toggle on to compare.
    # Laps are told apart by line style (Lap 1 solid, Lap 2 dashed), so the
    # colours can stay as channel identities on both.
    for name, *_ in CHANNELS:
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
            lap = lap_labels.get(ctrl['lap_var'].get())
            if lap is None:
                continue
            lap_df = df[df['Lap'] == lap].reset_index(drop=True)
            x = np.arange(len(lap_df)) * 0.01

            for name, label, _, _ in CHANNELS:
                if not ctrl[name]['on'].get():
                    continue
                y = smooth(channel_data(lap_df, name), ctrl[name]['sm'].get())
                ax.plot(x, y, color=ctrl[name]['col'].get(),
                        linewidth=ctrl[name]['w'].get(), linestyle=ls,
                        label=f"{tag} {label}")
                any_line = True

        ax.axhline(0, color="#cccccc", lw=0.8, zorder=0)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Acceleration (g)")
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