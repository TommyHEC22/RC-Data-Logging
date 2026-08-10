import pandas as pd
from V2_parser import convert_file_to_csv
import easygui
from matplotlib import pyplot as plt
import numpy as np

#file = easygui.fileopenbox()
#df = pd.read_csv(convert_file_to_csv(file))

df = pd.read_csv("DATA70.csv")
df['Time'] = df.groupby('Lap').cumcount() * 0.01

print(df.describe())

def get_laptimes_list(df):
    # First timestamp seen for each lap number
    laps = df.groupby('Lap')
    laptimes = []

    for lap in laps:
        end = lap[1].iloc[-1]['Time']
        start = lap[1].iloc[0]['Time']
        lap_time = end - start
        lap_time = float(lap_time)
        laptimes.append(lap_time)

    laptimes.pop(0) # Remove first lap time, as it is not a legit lap
    laptimes.pop(-1) # Remove last lap time, as it is not a legit lap

    return laptimes

def get_laptimes_dictionary(df):
    # First timestamp seen for each lap number
    laps = df.groupby('Lap')
    laptimes = {}

    for lap in laps:
        lap_num = lap[0]
        end = lap[1].iloc[-1]['Time']
        start = lap[1].iloc[0]['Time']
        lap_time = end - start
        lap_time = float(lap_time/1000)
        laptimes[lap_num] = lap_time

    first_lap_key = min(laptimes.keys())
    del laptimes[first_lap_key]
    
    last_lap_key = max(laptimes.keys())
    del laptimes[last_lap_key]

    return laptimes

laptimes = get_laptimes_list(df)
for i in range(len(laptimes)):
    print(i+1, ":", laptimes[i])

#Find fastest lap
ascending = sorted(laptimes)
print("Fastest:", ascending[0])

#Find average lap
average_lap = sum(laptimes) / len(laptimes)
average_lap = round(average_lap, 3)
print("Average:", average_lap)

#Best 2 consecutive
two_consecutive = 1000
for i in range(len(laptimes)-1):
    consec = laptimes[i] + laptimes[i+1]
    if consec < two_consecutive:
        two_consecutive = consec
two_consecutive = round(two_consecutive, 3)
print("Best 2 Consecutive:", two_consecutive)

#Best 3 consecutive
three_consecutive = 1000
for i in range(len(laptimes)-2):
    consec = laptimes[i] + laptimes[i+1] + laptimes[i+2]
    if consec < three_consecutive:
        three_consecutive = consec
three_consecutive = round(three_consecutive, 3)
print("Best 3 Consecutive:", three_consecutive)

#Find top 3 average
top_three_average = sum(ascending[0:3]) / 3
top_three_average = round(top_three_average, 3)
print("Top 3 Average:", top_three_average)

#Find top 5 average
top_five_average = sum(ascending[0:5]) / 5
top_five_average = round(top_five_average, 3)
print("Top 5 Average:", top_five_average)

#Find top 10 average
top_ten_average = sum(ascending[0:10]) / 10
top_ten_average = round(top_ten_average, 3)
print("Top 10 Average:", top_ten_average)

lap_numbers = np.arange(1, len(laptimes) + 1)
slope, intercept = np.polyfit(lap_numbers, laptimes, 1)
trendline = slope * lap_numbers + intercept

#Laptimes
plt.plot(lap_numbers, laptimes, 'o-', label='Actual Lap Times')
plt.plot(lap_numbers, trendline, '--r', label='Trendline (Best Fit)')
plt.xlabel('Lap Number')
plt.ylabel('Lap Time (s)')
plt.title('Lap Times')
plt.legend()
plt.show()


laps = get_laptimes_dictionary(df)
srted_laps = dict(sorted(laps.items(), key=lambda item: item[1]))
fast = list(srted_laps.keys())[:1]
top_5_lap_numbers = list(srted_laps.keys())[:5]
print("Top 5 Fastest Lap Numbers:", top_5_lap_numbers)

zing = df.groupby('Lap')
chosen = zing.get_group(8)

#Steering and yaw for chosen lap
plt.plot(chosen['Time'], chosen['Gyro Yaw'], label='Gyro Yaw')
plt.plot(chosen['Time'], chosen['Steering'], label='Steering', color='Brown')
plt.axhline(y=0, color='gray', linestyle='-', linewidth=1)
plt.xlabel('Timestamp')
plt.ylabel('Steering')
plt.title('Steering and yaw for Lap 2')
plt.legend()
plt.show()

top_5_df = df[df['Lap'].isin(top_5_lap_numbers)]
avg_steering = top_5_df.groupby('Time')['Steering'].mean()
avg_yaw = top_5_df.groupby('Time')['Gyro Yaw'].mean()

plt.plot(avg_steering.index, avg_steering.values, color='purple', linewidth=2, label='Top 5 Average')
plt.plot(chosen['Time'], chosen['Steering'], label='Best Steering')
plt.axhline(y=0, color='gray', linestyle='-', linewidth=1)
plt.xlabel('Time (s)')
plt.ylabel('Average Steering Input')
plt.title('Averaged Steering Profile Across Top 5 Fastest Laps')
plt.legend()
plt.show()

plt.plot(avg_yaw.index, avg_yaw.values, color='Green', linewidth=2, label='Top 5 Average')
plt.axhline(y=0, color='gray', linestyle='-', linewidth=1)
plt.xlabel('Time (s)')
plt.ylabel('Average Steering Input')
plt.title('Averaged Steering Profile Across Top 5 Fastest Laps')
plt.legend()
plt.show()