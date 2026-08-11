import tkinter as tk
from tkinter import ttk
from V2_parser import convert_file_to_csv
import easygui
import pandas as pd
import numpy as np

root = tk.Tk()
root.state("zoomed")
root.title("Race Engineer")

df = None

button = tk.Button(
    root,
    bg="#2d2d2d", fg="white",
    activebackground="#3d3d3d", activeforeground="white",
    relief="flat", bd=0,
    font=("Segoe UI", 11)
)

def show_loader():
    for w in root.winfo_children():
        w.destroy()
    tk.Label(root, text="Load a .clf file to analyze", font=("Segoe UI", 30)).pack(pady=(100, 10))
    ttk.Button(root, text="Load Data", command=load_data).pack(pady=20, ipadx=20, ipady=20)

def load_data():
    global df
    try:
        file = easygui.fileopenbox()
        df = pd.read_csv(convert_file_to_csv(file))
        print("Loaded" if len(df) > 100 else "Under 100 rows")
        show_analysis()          # swap to the next screen
    except Exception as e:
        print("Error loading file:", e)

def show_analysis():
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
    tk.Label(root, text=lines, justify="left").pack(padx=20, pady=20)


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

    tk.Label(root, text=f"Fastest Lap: {fastest_lap:.2f}s").pack(pady=10)
    tk.Label(root, text=f"Average Lap: {average_lap:.2f}s").pack(pady=10)
    tk.Label(root, text=f"Top 3 Average: {top_three_average:.2f}s").pack(pady=10)
    tk.Label(root, text=f"Top 5 Average: {top_five_average:.2f}s").pack(pady=10)
    tk.Label(root, text=f"Best 2 Consecutive Laps: {top_two_consecutive:.2f}s").pack(pady=10)
    tk.Label(root, text=f"Number of Bad Laps: {num_bobble_laps}").pack(pady=10)
    tk.Label(root, text=f"Trend: {get_trend(laptimes)}").pack(pady=10)
    tk.Label(root, text=f"Balance: {balance:.4f}").pack(pady=10)
    tk.Label(root, text=f"Cornering Grip: {corner:.4f}g").pack(pady=10)
    tk.Label(root, text=f"Exit Drive: {drive:.4f}g").pack(pady=10)


show_loader()
root.mainloop()