import os
import tkinter as tk
from macsafe import make_navbtn, force_light_mode
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")

GOOD, BAD, NEUTRAL = "#1a7f37", "#c0392b", "#777777"

# label, value format, unit, which direction is "better" (low / high / None)
SPECS = [
    ("Fastest Lap",        "{:.2f}", "s",     "low"),
    ("Average Lap",        "{:.2f}", "s",     "low"),
    ("Top 3 Average",      "{:.2f}", "s",     "low"),
    ("Top 5 Average",      "{:.2f}", "s",     "low"),
    ("Top 10 Average",     "{:.2f}", "s",     "low"),
    ("Best 2 Consecutive", "{:.2f}", "s",     "low"),
    ("Bad Laps",           "{:.0f}", "",      "low"),
    ("Average excluding bad laps", "{:.2f}", "s", "low"),
    ("Predicted Clean Runtime",  None,         "",     None),
    ("Balance",            "{:.4f}", "",      None),
    ("Cornering Grip",     "{:.4f}", "g",     "high"),
    ("Exit Drive",         "{:.4f}", "g",     "high"),
    ("Steering Rate",      "{:.0f}", " µs/s", None),
    ("Throttle Up",        "{:.0f}", " µs/s", None),
    ("Throttle Down",      "{:.0f}", " µs/s", None),
]


def compute_laptimes(src):
    """Lap times in seconds, keyed by lap number.

    Single source of truth for how a lap is timed, shared with every page so
    the whole app agrees with the Analysis figures: the gap from the start of
    one lap to the start of the next, taken from the real Timestamp, with the
    out lap and the unfinished final lap dropped.
    """
    df = src.copy().reset_index(drop=True)

    synthetic = df['Lap'].nunique() == 1
    if synthetic:
        edges = np.linspace(0, len(df), 5).astype(int)
        df['Lap'] = np.searchsorted(edges[1:-1], df.index, side='right')

    t = df['Timestamp'].astype(float) / 1000
    if not t.is_monotonic_increasing:
        t = t.cummax()

    starts = t.groupby(df['Lap']).first()
    laptimes = (starts.shift(-1) - starts).dropna()
    laptimes = laptimes.drop(index=df['Lap'].iloc[-1], errors='ignore')
    if not synthetic and len(laptimes) > 1:
        laptimes = laptimes.drop(index=laptimes.index[0])
    return laptimes.to_dict()


def compute_metrics(src):
    """All the analysis figures for one run, including the lap-times dict."""
    df = src.copy().reset_index(drop=True)

    synthetic = df['Lap'].nunique() == 1
    if synthetic:
        edges = np.linspace(0, len(df), 5).astype(int)
        df['Lap'] = np.searchsorted(edges[1:-1], df.index, side='right')

    t = df['Timestamp'].astype(float) / 1000
    if not t.is_monotonic_increasing:
        t = t.cummax()
    df['Time'] = t - t.groupby(df['Lap']).transform('first')

    laptimes = compute_laptimes(src)

    fastest = min(laptimes.values())
    average = sum(laptimes.values()) / len(laptimes)

    t3 = sorted(laptimes.values())[:3]
    top3 = sum(t3) / len(t3)
    t5 = sorted(laptimes.values())[:5]
    top5 = sum(t5) / len(t5)
    t10 = sorted(laptimes.values())[:10]
    top10 = sum(t10) / len(t10)

    best2 = 1000.0
    lap_numbers = sorted(laptimes.keys())
    for i in range(len(lap_numbers) - 1):
        pair = laptimes[lap_numbers[i]] + laptimes[lap_numbers[i + 1]]
        if pair < best2:
            best2 = pair

    bad = sum(1 for l in lap_numbers if laptimes[l] > fastest + 1.0)

    lappur = {l: t for l, t in laptimes.items() if t <= fastest + 1.0}

    goodaverage = sum(lappur.values()) / len(lappur)

    df_laps = df[df['Lap'].isin(lappur.keys())]

    def predicted_runtime(goodaverage):
        toge = True
        a = goodaverage
        count = 1
        while toge:
            if a > 300:
                toge = False
            else:
                count = count + 1
                a = a + goodaverage

        a = a - 300

        predicted = f"{count}/5:{a:.2f}"

        return predicted

    def yaw_balance(gyro_yaw, accel_y_g, w=15):
        yaw = np.convolve(np.asarray(gyro_yaw, float), np.ones(w) / w, 'same')
        ay = np.convolve(np.asarray(accel_y_g, float), np.ones(w) / w, 'same')
        mask = np.abs(ay) > 0.2
        s, _ = np.polyfit(ay[mask], yaw[mask], 1)
        return s

    def cornering_grip(accel_y_g, w=15):
        ay = np.convolve(np.abs(np.asarray(accel_y_g, float)), np.ones(w) / w, 'same')
        mask = ay > 0.2
        return np.percentile(ay[mask], 90)

    def exit_drive(accel_x_g, throttle_pct, steering_pct, w=15):
        # on throttle (> 5%) with the wheel roughly straight (|steer| < 20%)
        ax = np.convolve(np.abs(np.asarray(accel_x_g, float)), np.ones(w) / w, 'same')
        thr = np.asarray(throttle_pct, float)
        steer = np.asarray(steering_pct, float)
        mask = (thr > 5) & (np.abs(steer) < 20)
        return np.percentile(ax[mask], 90)

    bump = []
    for lap in lappur:
        z = df[df['Lap'] == lap]['Acceleration Z'].std()
        bump.append(z)
    std = sum(bump) / len(bump)

    dt = 0.01
    steer_rate = np.percentile(np.abs(np.diff(df_laps['Steering'].to_numpy(float))) / dt, 95)
    thr_diff = np.diff(df_laps['Throttle and brake'].to_numpy(float)) / dt
    thr_up = np.percentile(thr_diff[thr_diff > 0], 95)
    thr_down = np.percentile(-thr_diff[thr_diff < 0], 95)

    balance = yaw_balance(df_laps['Gyro Yaw'], df_laps['Acceleration Y'])
    corner = cornering_grip(df_laps['Acceleration Y'])
    drive = exit_drive(df_laps['Acceleration X'], df_laps['Throttle and brake'],
                       df_laps['Steering'])
    predictedruntime = predicted_runtime(goodaverage)

    return {
        'laptimes': laptimes,
        "Fastest Lap": fastest,
        "Average Lap": average,
        "Top 3 Average": top3,
        "Top 5 Average": top5,
        "Top 10 Average": top10,
        "Average excluding bad laps": goodaverage,
        "Best 2 Consecutive": best2,
        "Bad Laps": bad,
        "Balance": balance,
        "Cornering Grip": corner,
        "Exit Drive": drive,
        "Steering Rate": steer_rate,
        "Throttle Up": thr_up,
        "Throttle Down": thr_down,
        "Predicted Clean Runtime": predictedruntime
    }


def read_comment_file(path):
    """Plain-text run comment stashed next to the data ('' if missing/empty).

    main.py writes the main run's comment to comment_main.txt on load; comment.txt
    holds the comparison run's comment (written by the Comparison Run page and when
    a run is pushed into the df2 slot).
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""


def show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run, show_laptime_chart, show_channel_plot, show_prep_data):
    root.state("zoomed")
    for w in root.winfo_children():
        w.destroy()

    ma = compute_metrics(df)

    # comparison run, if one has been staged via the Comparison Run page
    mb = None
    if os.path.exists("df2.csv"):
        try:
            mb = compute_metrics(pd.read_csv("df2.csv"))
        except Exception as e:
            print("Could not use df2.csv for comparison:", e)
            mb = None

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    navbar = tk.Frame(container, bg="#1e1e1e", height=52)
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

    body = tk.Frame(container)
    body.pack(side="top", fill="both", expand=True, padx=20, pady=20)

    # ── main run: comment (top) + lap times (left) ───────
    main_col = tk.Frame(body)
    main_col.pack(side="left", fill="y", padx=(0, 20))

    main_comment = read_comment_file("comment_main.txt")
    if main_comment:
        tk.Label(main_col, text=main_comment, font=("Segoe UI", 10, "italic"),
                 fg="#555", wraplength=230, justify="left").pack(anchor="w", pady=(0, 6))

    laptimes_box = tk.LabelFrame(main_col, text="Lap Times (Main)",
                                 font=("Segoe UI", 12, "bold"), padx=10, pady=6)
    laptimes_box.pack(fill="y")
    for lap, t in ma['laptimes'].items():
        tk.Label(laptimes_box, text=f"Lap {lap}: {t:.2f}s",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=3)

    # ── comparison run: comment (top) + lap times (right) ─
    if mb is not None:
        df2_col = tk.Frame(body)
        df2_col.pack(side="right", fill="y", padx=(20, 0))

        df2_comment = read_comment_file("comment.txt")
        if df2_comment:
            tk.Label(df2_col, text=df2_comment, font=("Segoe UI", 10, "italic"),
                     fg="#555", wraplength=230, justify="left").pack(anchor="w", pady=(0, 6))

        df2_box = tk.LabelFrame(df2_col, text="Lap Times (df2)",
                                font=("Segoe UI", 12, "bold"), padx=10, pady=6)
        df2_box.pack(fill="y")
        for lap, t in mb['laptimes'].items():
            tk.Label(df2_box, text=f"Lap {lap}: {t:.2f}s",
                     font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=3)

    # ── stats grid (middle) ──────────────────────────────
    stats_area = tk.Frame(body)
    stats_area.pack(side="left", fill="both", expand=True)

    def stat_card(r, c, title, value, sub=None, sub_col=NEUTRAL):
        card = tk.Frame(stats_area, bg="white",
                        highlightbackground="#dcdcdc", highlightthickness=1, bd=0)
        card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
        tk.Label(card, text=title, font=("Segoe UI", 10), fg="#777",
                 bg="white").pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(card, text=value, font=("Segoe UI", 22, "bold"),
                 bg="white").pack(anchor="w", padx=14, pady=(0, 2 if sub else 12))
        if sub:
            tk.Label(card, text=sub, font=("Segoe UI", 11, "bold"),
                     fg=sub_col, bg="white").pack(anchor="w", padx=14, pady=(0, 12))

    def fmt_val(fmt, unit, val):
        return fmt.format(val) + unit if fmt else str(val)

    COLS = 6

    # main run cards
    for i, (label, fmt, unit, _better) in enumerate(SPECS):
        stat_card(i // COLS, i % COLS, label, fmt_val(fmt, unit, ma[label]))

    main_rows = (len(SPECS) + COLS - 1) // COLS

    # comparison cards below, with % change vs main
    if mb is not None:
        hdr = main_rows
        tk.Label(stats_area, text="Comparison Run (df2) — change vs main",
                 font=("Segoe UI", 11, "bold"), fg="#555").grid(
                     row=hdr, column=0, columnspan=COLS, sticky="w",
                     padx=8, pady=(20, 4))

        for i, (label, fmt, unit, better) in enumerate(SPECS):
            r = hdr + 1 + i // COLS
            c = i % COLS
            b_val = mb[label]
            val_txt = fmt_val(fmt, unit, b_val)

            if fmt is None:                       # non-numeric (Trend) → no %
                stat_card(r, c, label, val_txt)
                continue

            a_val = ma[label]
            if a_val == 0:
                stat_card(r, c, label, val_txt, "—", NEUTRAL)
                continue

            pct = (b_val - a_val) / abs(a_val) * 100.0
            sub = f"{pct:+.1f}%"
            if better == "low":
                col = GOOD if pct < 0 else BAD if pct > 0 else NEUTRAL
            elif better == "high":
                col = GOOD if pct > 0 else BAD if pct < 0 else NEUTRAL
            else:
                col = NEUTRAL
            stat_card(r, c, label, val_txt, sub, col)

    for c in range(COLS):
        stats_area.columnconfigure(c, weight=1, uniform="stat")