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

GOOD, BAD = "#1a7f37", "#c0392b"


def show_prep_data(root, df, show_analysis, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot):
    root.state("zoomed")
    for w in root.winfo_children():
        w.destroy()

    # every lap present (including out/in laps, so they can be binned here too);
    # timed the same way as the Analysis page - start of a lap to the start of
    # the next, from the real Timestamp - so the numbers match the rest of the
    # app. The out lap and the unfinished final lap have no "next start", so
    # they fall back to the span of their own samples.
    t = df['Timestamp'].astype(float) / 1000
    if not t.is_monotonic_increasing:
        t = t.cummax()
    df['Time'] = t - t.groupby(df['Lap']).transform('first')
    starts = t.groupby(df['Lap']).first()
    gaps = starts.shift(-1) - starts
    laptimes = {}
    for lap in sorted(df['Lap'].unique()):
        g = gaps.get(lap)
        if g is None or pd.isna(g):
            seg = t[df['Lap'] == lap]
            g = seg.iloc[-1] - seg.iloc[0]
        laptimes[lap] = float(g)

    deleted = set()          # lap numbers marked for deletion

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

    # ── lap list (left, scrollable) — click 🗑 to grey out ──
    laptimes_box = tk.LabelFrame(container, text="Lap Times  (🗑 to delete)",
                                 font=("Segoe UI", 12, "bold"), padx=6, pady=6)
    laptimes_box.pack(side="left", fill="y", padx=(10, 0), pady=10)

    list_canvas = tk.Canvas(laptimes_box, highlightthickness=0, width=230)
    scrollbar = ttk.Scrollbar(laptimes_box, orient="vertical", command=list_canvas.yview)
    list_inner = tk.Frame(list_canvas)
    list_inner.bind("<Configure>",
                    lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
    list_canvas.create_window((0, 0), window=list_inner, anchor="nw")
    list_canvas.configure(yscrollcommand=scrollbar.set)
    list_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    labels = {}

    def toggle_delete(lap):
        if lap in deleted:
            deleted.discard(lap)
            labels[lap].config(fg="#000000")
        else:
            deleted.add(lap)
            labels[lap].config(fg="#c0c0c0")      # greyed out

    for lap in sorted(laptimes):
        row = tk.Frame(list_inner)
        row.pack(fill="x", padx=4, pady=2)
        lbl = tk.Label(row, text=f"Lap {lap}: {laptimes[lap]:.2f}s",
                       font=("Segoe UI", 11), width=16, anchor="w")
        lbl.pack(side="left")
        tk.Button(row, text="🗑", font=("Segoe UI", 10),
                  fg=BAD, relief="flat", bd=0, cursor="hand2",
                  command=lambda l=lap: toggle_delete(l)).pack(side="right")
        labels[lap] = lbl

    # ── main area (right): throttle trace + trim sliders + save ──
    main = tk.Frame(container)
    main.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    n = len(df)
    throttle = df['Throttle and brake'].to_numpy(float)
    xs = np.arange(n)

    graph_frame = tk.Frame(main)
    graph_frame.pack(side="top", fill="both", expand=True)

    fig = Figure(figsize=(10, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(xs, throttle, color="#D93A00", linewidth=0.7)
    ax.set_xlabel("Sample")
    ax.set_ylabel("Throttle (µs)")
    ax.set_title("Full run — drag the sliders to trim the ends")
    ax.margins(x=0)
    ax.grid(alpha=0.3)

    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side="bottom", fill="x")

    start_var = tk.IntVar(value=0)
    end_var = tk.IntVar(value=n - 1)

    trim_artists = []

    def update_trim(*_):
        for a in trim_artists:
            a.remove()
        trim_artists.clear()
        lo, hi = sorted((start_var.get(), end_var.get()))
        if lo > 0:
            trim_artists.append(ax.axvspan(0, lo, color=BAD, alpha=0.15))
        if hi < n - 1:
            trim_artists.append(ax.axvspan(hi, n - 1, color=BAD, alpha=0.15))
        trim_artists.append(ax.axvline(lo, color=BAD, lw=1.5))
        trim_artists.append(ax.axvline(hi, color=BAD, lw=1.5))
        canvas.draw_idle()

    slider_frame = tk.Frame(main)
    slider_frame.pack(side="top", fill="x", pady=(10, 0))

    tk.Scale(slider_frame, from_=0, to=n - 1, orient="horizontal",
             variable=start_var, command=update_trim, label="Trim start",
             sliderlength=44, width=24, font=("Segoe UI", 10)).pack(fill="x")
    tk.Scale(slider_frame, from_=0, to=n - 1, orient="horizontal",
             variable=end_var, command=update_trim, label="Trim end",
             sliderlength=44, width=24, font=("Segoe UI", 10)).pack(fill="x")

    # ── bottom: save + status ────────────────────────────
    bottom = tk.Frame(main)
    bottom.pack(side="top", fill="x", pady=(10, 0))

    status = tk.Label(bottom, text="", font=("Segoe UI", 11))

    def save():
        lo, hi = sorted((start_var.get(), end_var.get()))
        pos = np.arange(len(df))
        keep = (pos >= lo) & (pos <= hi) & (~df['Lap'].isin(deleted).values)
        if not keep.any():
            status.config(text="Nothing left to save — check your trim/deletions.", fg=BAD)
            return

        cleaned = df[keep].reset_index(drop=True)
        cleaned.to_csv("df.csv", index=False)

        # apply to the live run so every page uses the cleaned data
        df.drop(df.index[~keep], inplace=True)
        df.reset_index(drop=True, inplace=True)
        print(f"Saved df.csv — {len(df)} rows kept "
              f"({len(deleted)} laps deleted, trimmed to samples {lo}–{hi})")

        # re-render so the list, trace and sliders reflect the cleaned run
        show_prep_data(root, df, show_analysis, show_steeringthrottle_graph,
                       show_friction_circle, show_gforces, show_histograms,
                       show_loader, show_load_df2, show_save_run,
                       show_laptime_chart, show_channel_plot)

    tk.Button(bottom, text="Save cleaned run", command=save,
              bg="#2d2d2d", fg="white",
              activebackground="#3d3d3d", activeforeground="white",
              relief="flat", bd=0, font=("Segoe UI", 12),
              padx=30, pady=12, cursor="hand2").pack(side="left")
    status.pack(side="left", padx=14)

    update_trim()