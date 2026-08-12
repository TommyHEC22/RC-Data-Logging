import os
import tkinter as tk
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
    ("Best 2 Consecutive", "{:.2f}", "s",     "low"),
    ("Bad Laps",           "{:.0f}", "",      "low"),
    ("Trend",              None,     "",      None),
    ("Balance",            "{:.4f}", "",      None),
    ("Cornering Grip",     "{:.4f}", "g",     "high"),
    ("Exit Drive",         "{:.4f}", "g",     "high"),
    ("Steering Rate",      "{:.0f}", " µs/s", None),
    ("Throttle Up",        "{:.0f}", " µs/s", None),
    ("Throttle Down",      "{:.0f}", " µs/s", None),
]


def compute_metrics(src):
    """All the analysis figures for one run, including the lap-times dict."""
    df = src.copy()
    df['Time'] = df.groupby('Lap').cumcount() * 0.01

    laps = df.groupby('Lap')
    laptimes = {}
    for lap in laps:
        end = lap[1].iloc[-1]['Time']
        start = lap[1].iloc[0]['Time']
        laptimes[lap[0]] = float(end - start)
    del laptimes[min(laptimes.keys())]
    del laptimes[max(laptimes.keys())]

    fastest = min(laptimes.values())
    average = sum(laptimes.values()) / len(laptimes)

    t3 = sorted(laptimes.values())[:3]
    top3 = sum(t3) / len(t3)
    t5 = sorted(laptimes.values())[:5]
    top5 = sum(t5) / len(t5)

    best2 = 1000.0
    lap_numbers = sorted(laptimes.keys())
    for i in range(len(lap_numbers) - 1):
        pair = laptimes[lap_numbers[i]] + laptimes[lap_numbers[i + 1]]
        if pair < best2:
            best2 = pair

    bad = sum(1 for l in lap_numbers if laptimes[l] > fastest + 1.0)

    lappur = {l: t for l, t in laptimes.items() if t <= fastest + 1.0}
    slope, _ = np.polyfit(np.array(list(lappur.keys())),
                          np.array(list(lappur.values())), 1)
    if slope < -0.05:
        trend = "Improving"
    elif slope > 0.05:
        trend = "Dropping off"
    else:
        trend = "Consistent"

    valid_laps = sorted(df['Lap'].unique())[1:-1]
    df_laps = df[df['Lap'].isin(valid_laps)]

    def yaw_balance(gyro_yaw, accel_y_g, w=15):
        yaw = np.convolve(np.asarray(gyro_yaw, float), np.ones(w) / w, 'same')
        ay = np.convolve(np.asarray(accel_y_g, float), np.ones(w) / w, 'same')
        mask = np.abs(ay) > 0.2
        s, _ = np.polyfit(ay[mask], yaw[mask], 1)
        return s

    def cornering_grip(accel_y_g, speed_kmh=None, w=15):
        ay = np.convolve(np.abs(np.asarray(accel_y_g, float)), np.ones(w) / w, 'same')
        mask = ay > 0.2
        if speed_kmh is not None:
            mask &= np.asarray(speed_kmh) > 5
        return np.percentile(ay[mask], 90)

    def exit_drive(accel_x_g, throttle_us, throttle_centre, accel_y_g, w=15):
        ax = np.convolve(np.abs(np.asarray(accel_x_g, float)), np.ones(w) / w, 'same')
        thr = np.asarray(throttle_us, float) - throttle_centre
        mask = (thr > 0) & (np.abs(np.asarray(accel_y_g)) < 0.6)
        return np.percentile(ax[mask], 90)

    dt = 0.01
    steer_rate = np.percentile(np.abs(np.diff(df_laps['Steering'].to_numpy(float))) / dt, 95)
    thr_diff = np.diff(df_laps['Throttle and brake'].to_numpy(float)) / dt
    thr_up = np.percentile(thr_diff[thr_diff > 0], 95)
    thr_down = np.percentile(-thr_diff[thr_diff < 0], 95)

    throttle_centre = np.median(df_laps['Throttle and brake'])
    balance = yaw_balance(df_laps['Gyro Yaw'], df_laps['Acceleration Y'])
    corner = cornering_grip(df_laps['Acceleration Y'], df_laps['Speed all'])
    drive = exit_drive(df_laps['Acceleration X'], df_laps['Throttle and brake'],
                       throttle_centre, df_laps['Acceleration Y'])

    return {
        'laptimes': laptimes,
        "Fastest Lap": fastest,
        "Average Lap": average,
        "Top 3 Average": top3,
        "Top 5 Average": top5,
        "Best 2 Consecutive": best2,
        "Bad Laps": bad,
        "Trend": trend,
        "Balance": balance,
        "Cornering Grip": corner,
        "Exit Drive": drive,
        "Steering Rate": steer_rate,
        "Throttle Up": thr_up,
        "Throttle Down": thr_down,
    }


def show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces, show_histograms, show_loader, show_load_df2, show_save_run):
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

    body = tk.Frame(container)
    body.pack(side="top", fill="both", expand=True, padx=20, pady=20)

    # ── main run lap times (left) ────────────────────────
    laptimes_box = tk.LabelFrame(body, text="Lap Times (Main)",
                                 font=("Segoe UI", 12, "bold"), padx=10, pady=6)
    laptimes_box.pack(side="left", fill="y", padx=(0, 20))
    for lap, t in ma['laptimes'].items():
        tk.Label(laptimes_box, text=f"Lap {lap}: {t:.2f}s",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=3)

    # ── comparison run lap times (right) ─────────────────
    if mb is not None:
        df2_box = tk.LabelFrame(body, text="Lap Times (df2)",
                                font=("Segoe UI", 12, "bold"), padx=10, pady=6)
        df2_box.pack(side="right", fill="y", padx=(20, 0))
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

    COLS = 5

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