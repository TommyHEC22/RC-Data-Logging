# Datalogger

Data logger takes the raw .clf files from the testlogger mini device and convert it into a csv file and gives the user visualizations and analysis on the data. This is for any rc car fitted with a testlogger mini.

## Why i built this

I built this software as no other tool that exists has the full deep dive analysis like the analytics page does here. I wanted to see more clearly exactly how my runs compared to one another and how the car and the driver behaved differently run to run along with all the usual visualizations.

## What it does

This takes the raw clf file from the sd card and runs it through a parser to convert it into a raw csv file of data. It then shows the users analysis pages and visualizations of the data from that run, it also allows for comparissons between runs. Users can save runs with notes to remond themselves what they changed for each run and how they felt the car behaved differently or their interpretation of what the data from that run shows.

## How it works

The frontend very simply uses tkinter with visualisations done my matplotlib. Each laptime is is claculated based on the Laptrigstatus in the data, only the laps are kept in the data with each end of the raw data being chopped off. From the list of laptimes, a 'good' lap is a lap that is within one second of the best and these are the laps used to calculate predicted runtime and the other metrics such as cornering G. 

- The cornering g is calculated by taking the Acceleration Y (lateral acceleration) that is greater than 0.2g (throwing away straights and non movement). It then takes the 90% of this data to cut out major spikes. A 15 sample moving average was used to clean up the very messy data caused by vibrations in the vehicle.

- The exit drive uses the same logic. The only difference is that it only keeps samples where throttle is above 5 and steering is within +-20 percent of throw. The braking version just uses the examples where braking is above 5.

- Balance using the same 15 ample moving average of the yaw and lateral acceleration again only keeping samples above 0.2g. It then plots yaw rate against lateral g and fits a straight line using polyfit. The slope of this line gives us our value in deg/s

Runs are saved by adding a comment to the top of the csv file.

## Problems i hit

The raw data is EXTREMELY messy, i think this is due to internal vibrations picked up by the sensors. The only way arounf this is to smooth the data. A slider for smoothing was added to plots to allow the user to control how much of this to use and after having a mess myself, the 15 used for the analysis metrics looked like it just cleaned up the noise nicely.

For custom plots, some graphs use much greater values than others against the time, this means to compare them, one just looks like a flat line almost at 0. To combat this, amplification was added to make both plots more visable at once.

Another issue was that sometimes the lap counter double counted when the car passed by at another section of track near the line. This was a huge issue as it would leave invalid laps in the data. To stop this being a problem, the data cleaning section was added. This allowed users to delete laps which were clearly invalid making their optimum runtime predictions and consecutive lap metrics accurate again.

## Results

This software has proven useful to myself and my team is understanding how certain setup changes effect the potential within the car. Somemtimes as a driver you cannot feel the laptime like you think you can so to be able to see how the laptimes are effected and why is critical in understanding what the changes are doing. It has alo proved useful in comparing dta between drivers to get the most out of a driver on a day they are struggling compared to a teammate.

## Tech
- Python, Matplotlib, Tkinter, NumPy, pandas, easygui, PyInstaller.

## How to run

Download the most recent version in releases.