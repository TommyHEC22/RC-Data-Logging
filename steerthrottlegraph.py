import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces):
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

    navbtn("Analysis", lambda: show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces))
    navbtn("Steering & Throttle", lambda: show_steeringthrottle_graph(root, df, show_analysis, show_friction_circle, show_gforces))
    navbtn("Friction Circle", lambda: show_friction_circle(root, df, show_analysis, show_steeringthrottle_graph, show_gforces))
    navbtn("G-Forces", lambda: show_gforces(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle))

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

        for name, default_col in (('steer', COLOURS[0]), ('thr', COLOURS[1])):
            block = tk.LabelFrame(frame,
                                  text="Steering" if name == 'steer' else "Throttle")
            block.pack(padx=8, pady=6, fill="x")

            on = tk.BooleanVar(value=True)
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
            width.set(1.5); width.pack(fill="x")

            sm = tk.Scale(block, from_=1, to=101, resolution=2,
                          orient="horizontal", label="Smoothing",
                          command=lambda v: draw())
            sm.set(1); sm.pack(fill="x")

            c[name] = {'on': on, 'col': col, 'w': width, 'sm': sm}

        return frame, c

    left_frame, left = build_panel(container, "Lap 1")
    left_frame.pack(side="left", fill="y", padx=10)

    right_frame, right = build_panel(container, "Lap 2")
    right_frame.pack(side="right", fill="y", padx=10)

    # default lap 2 to distinct colours so the two laps don't clash
    right['steer']['col'].set(COLOURS[2])
    right['thr']['col'].set(COLOURS[3])

    # ── figure in the middle (with zoom toolbar) ─────────────
    graph_frame = tk.Frame(container)
    graph_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    fig = Figure(figsize=(9, 5), dpi=100)
    ax = fig.add_subplot(111)
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

        any_line = False
        for ctrl, tag in ((left, "L1"), (right, "L2")):
            lap = lap_labels.get(ctrl['lap_var'].get())
            if lap is None:
                continue
            lap_df = df[df['Lap'] == lap].reset_index(drop=True)
            x = np.arange(len(lap_df)) * 0.01

            if ctrl['steer']['on'].get():
                y = smooth(lap_df['Steering'].values, ctrl['steer']['sm'].get())
                ax.plot(x, y, color=ctrl['steer']['col'].get(),
                        linewidth=ctrl['steer']['w'].get(), label=f"{tag} Steering")
                any_line = True

            if ctrl['thr']['on'].get():
                y = smooth(lap_df['Throttle and brake'].values, ctrl['thr']['sm'].get())
                ax.plot(x, y, color=ctrl['thr']['col'].get(),
                        linewidth=ctrl['thr']['w'].get(), label=f"{tag} Throttle")
                any_line = True

        ax.set_xlabel("Time (s)")
        if any_line:
            ax.legend(loc="upper right")
        ax.grid(alpha=0.3)

        # restore the zoom the user had, unless this is the very first draw
        if had_data:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        canvas.draw()

    for ctrl in (left, right):
        ctrl['lap_var'].trace_add("write", lambda *_: draw())

    draw()