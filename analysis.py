import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")

def show_analysis(root, df, show_steeringthrottle_graph, show_friction_circle, show_gforces):
    for w in root.winfo_children():
        w.destroy()

    def get_laptimes_dictionary(df):
        # First timestamp seen for each lap number
        laps = df.groupby('Lap')
        laptimes = {}

        for lap in laps:
            lap_num = lap[0]
            end = lap[1].iloc[-1]['Time']
            start = lap[1].iloc[0]['Time']
            lap_time = end - start
            lap_time = float(lap_time)
            laptimes[lap_num] = lap_time

        first_lap_key = min(laptimes.keys())
        del laptimes[first_lap_key]
        
        last_lap_key = max(laptimes.keys())
        del laptimes[last_lap_key]

        return laptimes

    df['Time'] = df.groupby('Lap').cumcount() * 0.01

    laptimes = get_laptimes_dictionary(df)

    lines = "\n".join(f"Lap {lap}: {t:.2f}s" for lap, t in laptimes.items())

    fastest_lap = min(laptimes.values())
    average_lap = sum(laptimes.values()) / len(laptimes)

    top_three_average = sorted(laptimes.values())[:3]
    top_three_average = sum(top_three_average) / len(top_three_average)

    top_five_average = sorted(laptimes.values())[:5]
    top_five_average = sum(top_five_average) / len(top_five_average)

    top_two_consecutive = 1000
    lap_numbers = sorted(laptimes.keys())
    for i in range(len(lap_numbers) - 1):
        lap1 = laptimes[lap_numbers[i]]
        lap2 = laptimes[lap_numbers[i + 1]]
        if (lap1 + lap2) < top_two_consecutive:
            top_two_consecutive = lap1 + lap2

    num_bobble_laps = 0
    for i in range(len(lap_numbers)):
        if laptimes[lap_numbers[i]] > (fastest_lap + 1.0):
            num_bobble_laps += 1

    def get_trend(laptimes):
        fastest_lap = min(laptimes.values())

        # keep only laps within 1.0s of the fastest
        lappur = {lap: t for lap, t in laptimes.items() if t <= fastest_lap + 1.0}

        laps = np.array(list(lappur.keys()))
        times = np.array(list(lappur.values()))
        slope, intercept = np.polyfit(laps, times, 1)

        threshold = 0.05
        if slope < -threshold:
            trend = "Improving"
        elif slope > threshold:
            trend = "Dropping off"
        else:
            trend = "Consistent"

        return trend

    valid_laps = sorted(df['Lap'].unique())[1:-1]
    df_laps = df[df['Lap'].isin(valid_laps)]

    def yaw_balance(gyro_yaw, accel_y_g, w=15):   # bigger number is more rotation
        yaw = np.convolve(np.asarray(gyro_yaw, float), np.ones(w)/w, 'same')   # deg/s
        ay  = np.convolve(np.asarray(accel_y_g, float), np.ones(w)/w, 'same')  # g

        # both signed the same way in a turn — no fold needed
        mask = np.abs(ay) > 0.2        # committed cornering only
        x, y = ay[mask], yaw[mask]

        slope, intercept = np.polyfit(x, y, 1)

        return slope

    def cornering_grip(accel_y_g, speed_kmh=None, w=15):
        """Overall lateral grip / constant-cornering ability.
        Higher = more grip (car holds more lateral g)."""
        ay = np.convolve(np.abs(np.asarray(accel_y_g, float)), np.ones(w)/w, 'same')

        mask = ay > 0.2                       # cornering only, drop straights
        if speed_kmh is not None:
            mask &= np.asarray(speed_kmh) > 5
        ay = ay[mask]

        return np.percentile(ay, 90)          # the lateral-g ceiling you sustain


    def exit_drive(accel_x_g, throttle_us, throttle_centre, accel_y_g, w=15):
        """Flat-out rear-end straight-line corner-exit drive.
        Higher = more forward grip put down on exit."""
        ax  = np.convolve(np.abs(np.asarray(accel_x_g, float)), np.ones(w)/w, 'same')
        thr = np.asarray(throttle_us, float) - throttle_centre

        mask = (thr > 0) & (np.abs(np.asarray(accel_y_g)) < 0.6)   # on power, exit-ish
        ax = ax[mask]

        return np.percentile(ax, 90)          # forward-g ceiling on drive

    throttle_centre = np.median(df_laps['Throttle and brake'])

    balance = yaw_balance(df_laps['Gyro Yaw'], df_laps['Acceleration Y'])
    corner = cornering_grip(df_laps['Acceleration Y'], df_laps['Speed all'])
    drive  = exit_drive(df_laps['Acceleration X'], df_laps['Throttle and brake'],throttle_centre, df_laps['Acceleration Y'])

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    navbar = tk.Frame(container, bg="#1e1e1e", height=52)
    navbar.pack(side="top", fill="x")
    navbar.pack_propagate(False)          # keep the 52px height

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

    body = tk.Frame(container)
    body.pack(side="top", fill="both", expand=True, padx=20, pady=20)

    laptimes_box = tk.LabelFrame(body, text="Lap Times",
                                 font=("Segoe UI", 12, "bold"), padx=10, pady=6)
    laptimes_box.pack(side="left", fill="y", padx=(0, 20))

    for lap, t in laptimes.items():
        tk.Label(laptimes_box, text=f"Lap {lap}: {t:.2f}s",
                 font=("Segoe UI", 11)).pack(anchor="w", padx=10, pady=3)

    stats_area = tk.Frame(body)
    stats_area.pack(side="left", fill="both", expand=True)

    def stat_card(title, value, r, c):
        card = tk.Frame(stats_area, bg="white",
                        highlightbackground="#dcdcdc", highlightthickness=1, bd=0)
        card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
        tk.Label(card, text=title, font=("Segoe UI", 10), fg="#777",
                 bg="white").pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(card, text=value, font=("Segoe UI", 22, "bold"),
                 bg="white").pack(anchor="w", padx=14, pady=(0, 12))

    stats = [
        ("Fastest Lap",        f"{fastest_lap:.2f}s"),
        ("Average Lap",        f"{average_lap:.2f}s"),
        ("Top 3 Average",      f"{top_three_average:.2f}s"),
        ("Top 5 Average",      f"{top_five_average:.2f}s"),
        ("Best 2 Consecutive", f"{top_two_consecutive:.2f}s"),
        ("Bad Laps",           f"{num_bobble_laps}"),
        ("Trend",              get_trend(laptimes)),
        ("Balance",            f"{balance:.4f}"),
        ("Cornering Grip",     f"{corner:.4f}g"),
        ("Exit Drive",         f"{drive:.4f}g"),
    ]

    COLS = 5
    for i, (title, value) in enumerate(stats):
        stat_card(title, value, i // COLS, i % COLS)

    for c in range(COLS):
        stats_area.columnconfigure(c, weight=1, uniform="stat")