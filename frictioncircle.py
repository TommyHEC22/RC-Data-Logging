import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run):
    root.state("zoomed")
    for w in root.winfo_children():
        w.destroy()

    # ── lap times (for the selector labels) ──────────────────
    valid_laps = sorted(df['Lap'].unique())[1:-1]

    def get_laptimes_dictionary(df):
        laps = df.groupby('Lap')
        laptimes = {}
        for lap in laps:
            end = lap[1].iloc[-1]['Time']
            start = lap[1].iloc[0]['Time']
            laptimes[lap[0]] = float(end - start)
        del laptimes[min(laptimes.keys())]
        del laptimes[max(laptimes.keys())]
        return laptimes

    df['Time'] = df.groupby('Lap').cumcount() * 0.01
    laptimes = get_laptimes_dictionary(df)
    lap_labels = {f"Lap {l} — {laptimes[l]:.2f}s": l for l in valid_laps}
    lap_labels = {"All laps": None, **lap_labels}          # add an all-laps option

    COLOURS = ["#002AFF", "#D93A00", '#2E8B00', "#CA004A", "#600076", '#000000']

    def smooth(data, w):
        w = int(w)
        if w <= 1:
            return np.asarray(data, float)
        return np.convolve(np.asarray(data, float), np.ones(w) / w, mode='same')

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
    navbtn("Comparison Run", lambda: show_load_df2(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_save_run))
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader, show_load_df2, show_save_run))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader, show_load_df2, show_save_run))
    navbtn("Save Run", lambda: show_save_run(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2))

    container = tk.Frame(outer)
    container.pack(fill="both", expand=True)

    # ── control panel (left) ─────────────────────────────
    def build_panel(parent, title, default_index, default_col, default_on):
        frame = tk.Frame(parent, bd=1, relief="groove")
        tk.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(pady=5)

        keys = list(lap_labels)
        lap_var = tk.StringVar(value=keys[default_index])
        ttk.Combobox(frame, textvariable=lap_var, values=keys,
                     state="readonly", width=16).pack(pady=5)

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

    # A defaults to all laps (context blob); B to the first lap, off until wanted
    left_frame, left = build_panel(controls, "Lap A", 0, COLOURS[0], True)
    left_frame.pack(fill="x", pady=(0, 10))

    right_frame, right = build_panel(controls, "Lap B", 1, COLOURS[2], False)
    right_frame.pack(fill="x")

    # display options
    opts = tk.LabelFrame(controls, text="Display")
    opts.pack(fill="x", pady=10)

    size = tk.Scale(opts, from_=1, to=20, resolution=1,
                    orient="horizontal", label="Point size",
                    command=lambda v: draw())
    size.set(3); size.pack(fill="x")

    smoothing = tk.Scale(opts, from_=1, to=51, resolution=2,
                         orient="horizontal", label="Smoothing",
                         command=lambda v: draw())
    smoothing.set(15); smoothing.pack(fill="x")     # matches the analysis metrics' window

    show_rings = tk.BooleanVar(value=True)
    tk.Checkbutton(opts, text="Reference circles", variable=show_rings,
                   command=lambda: draw()).pack(anchor="w")

    # ── figure (middle) ──────────────────────────────────
    graph_frame = tk.Frame(container)
    graph_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fig = Figure(figsize=(7, 7), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")

    def points_for(ctrl):
        lap = lap_labels.get(ctrl['lap_var'].get())
        if lap is None:                                  # "All laps"
            sub = df[df['Lap'].isin(valid_laps)]
        else:
            sub = df[df['Lap'] == lap]
        # x = lateral (Y), y = longitudinal (X) — smoothed to strip vibration
        w = smoothing.get()
        return (smooth(sub['Acceleration Y'].values, w),
                smooth(sub['Acceleration X'].values, w))

    def draw():
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        had_data = ax.has_data()

        ax.clear()

        max_g = 1.0
        for ctrl, tag in ((left, "A"), (right, "B")):
            if not ctrl['on'].get():
                continue
            ay, ax_long = points_for(ctrl)
            ax.scatter(ay, ax_long, s=size.get(), alpha=0.35,
                       color=ctrl['col'].get(), edgecolors='none',
                       label=f"Lap {tag}")
            if len(ay):
                max_g = max(max_g,
                            np.nanpercentile(np.abs(ay), 99),
                            np.nanpercentile(np.abs(ax_long), 99))

        lim = np.ceil(max_g * 2) / 2 + 0.25          # tidy round-up for the axes

        # reference rings at 0.5g intervals
        if show_rings.get():
            theta = np.linspace(0, 2 * np.pi, 200)
            g = 0.5
            while g <= lim:
                ax.plot(g * np.cos(theta), g * np.sin(theta),
                        color="#bbbbbb", lw=0.8, zorder=0)
                ax.text(0, g, f"{g:g}g", color="#999", fontsize=8,
                        ha="center", va="bottom", zorder=0)
                g += 0.5

        ax.axhline(0, color="#dddddd", lw=0.8, zorder=0)
        ax.axvline(0, color="#dddddd", lw=0.8, zorder=0)

        ax.set_xlabel("Lateral g  (Acceleration Y)")
        ax.set_ylabel("Longitudinal g  (Acceleration X)")
        ax.set_aspect('equal')          # ← makes the circle actually circular
        if left['on'].get() or right['on'].get():
            ax.legend(loc="upper right")

        if had_data:
            ax.set_xlim(xlim); ax.set_ylim(ylim)
        else:
            ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)

        canvas.draw()

    for ctrl in (left, right):
        ctrl['lap_var'].trace_add("write", lambda *_: draw())

    draw()