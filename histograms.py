import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader):
    root.state("zoomed")
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
    lap_labels = {"All laps": None, **lap_labels}

    COLOURS = ["#002AFF", "#D93A00", '#2E8B00', "#CA004A", "#600076", '#000000']

    # reference line at the halfway point between min and max pulse width
    driven = df[df['Lap'].isin(valid_laps)]
    steer_centre = float((driven['Steering'].min() + driven['Steering'].max()) / 2)
    thr_centre   = float((driven['Throttle and brake'].min() + driven['Throttle and brake'].max()) / 2)

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
    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces, show_histograms, show_loader))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces, show_histograms, show_loader))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_histograms, show_loader))
    navbtn("Histograms", lambda: show_histograms(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_loader))

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

    left_frame, left = build_panel(controls, "Lap A", 0, COLOURS[0], True)   # all laps
    left_frame.pack(fill="x", pady=(0, 10))

    right_frame, right = build_panel(controls, "Lap B", 1, COLOURS[1], False)
    right_frame.pack(fill="x")

    # display options
    opts = tk.LabelFrame(controls, text="Display")
    opts.pack(fill="x", pady=10)

    bins = tk.Scale(opts, from_=10, to=100, resolution=5,
                    orient="horizontal", label="Bins",
                    command=lambda v: draw())
    bins.set(40); bins.pack(fill="x")

    normalise = tk.BooleanVar(value=True)
    tk.Checkbutton(opts, text="Normalise (% of lap)", variable=normalise,
                   command=lambda: draw()).pack(anchor="w")

    # ── figure (middle): two histograms side by side ─────
    graph_frame = tk.Frame(container)
    graph_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fig = Figure(figsize=(10, 5), dpi=100)
    ax_s = fig.add_subplot(1, 2, 1)      # steering
    ax_t = fig.add_subplot(1, 2, 2)      # throttle & brake
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")

    def subset(ctrl):
        lap = lap_labels.get(ctrl['lap_var'].get())
        if lap is None:                              # "All laps"
            return df[df['Lap'].isin(valid_laps)]
        return df[df['Lap'] == lap]

    def draw():
        ax_s.clear()
        ax_t.clear()

        any_line = False
        for ctrl, tag in ((left, "A"), (right, "B")):
            if not ctrl['on'].get():
                continue
            data = subset(ctrl)
            steer = data['Steering'].to_numpy(float)
            thr   = data['Throttle and brake'].to_numpy(float)
            colour = ctrl['col'].get()

            w_s = np.ones(len(steer)) / len(steer) * 100 if normalise.get() else None
            w_t = np.ones(len(thr)) / len(thr) * 100 if normalise.get() else None

            ax_s.hist(steer, bins=int(bins.get()), color=colour, alpha=0.45,
                      weights=w_s, edgecolor=colour, label=f"Lap {tag}")
            ax_t.hist(thr, bins=int(bins.get()), color=colour, alpha=0.45,
                      weights=w_t, edgecolor=colour, label=f"Lap {tag}")
            any_line = True

        # neutral reference lines
        ax_s.axvline(steer_centre, color="#999999", lw=1, linestyle="--")
        ax_t.axvline(thr_centre, color="#999999", lw=1, linestyle="--")

        ylab = "% of lap" if normalise.get() else "Samples"
        ax_s.set_title("Steering")
        ax_s.set_xlabel("Pulse width (µs)")
        ax_s.set_ylabel(ylab)
        ax_t.set_title("Throttle & Brake")
        ax_t.set_xlabel("Pulse width (µs)")
        ax_t.set_ylabel(ylab)

        for a in (ax_s, ax_t):
            a.grid(alpha=0.3)
            if any_line:
                a.legend(loc="upper right", fontsize=8)

        fig.tight_layout()
        canvas.draw()

    for ctrl in (left, right):
        ctrl['lap_var'].trace_add("write", lambda *_: draw())

    draw()