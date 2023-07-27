import pandas as pd
import numpy as np
import scipy
from scipy.stats import norm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.interpolate import make_interp_spline
from datetime import datetime, timedelta, date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import time
import random
import os
from tkinter import Tk, Label, Button, OptionMenu, StringVar, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


pd.options.display.float_format = '{:,.4f}'.format


#Create the main Tkinter application
root = Tk()
root.title("Vanna/Gamma Exposure Visualization")
root.geometry("1200x800")

def calculateAndDisplay():
    selectedDate = datetime.strptime(selectedDateVar.get(), '%Y-%m-%d')
    # selectedDate = selectedDate.replace(hour=16)
    # Filter data based on selected expiration date
    filteredDf = df[df['ExpirationDate'] == selectedDate]
    print(filteredDf)
    dfAgg = filteredDf.groupby(['StrikePrice'])[['Vanna', 'CallGEX', 'PutGEX', 'TotalGamma']].sum()
    strikes = dfAgg.index.values
    
    # Create three subplots within one figure
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Vanna/Gamma Exposure Visualization", fontsize=16)
    fig.set_facecolor('black')

    # Call and Put Gamma Display
    xnew = np.linspace(strikes.min(), strikes.max(), 500)  # Smooth x values for interpolation
    spl = make_interp_spline(strikes, dfAgg['Vanna'].to_numpy(), k=5)
    ynew = spl(xnew)
    axs[0].plot(xnew, ynew, linewidth=1.5, label="Total Vanna", color='green')    #Plot Chart
    axs[0].set_title("Vanna", color='white')
    axs[0].set_xlabel('Strike', color='white')
    axs[0].set_ylabel('Total Vanna, $', color='white')
    axs[0].set_facecolor('black')
    axs[0].axhline(y=0, color='white', lw=0.5)
    axs[0].grid(True, linestyle='dashed', lw=0.3)
    axs[0].set_xlim([fromStrike, toStrike])
    axs[0].yaxis.set_major_formatter(ticker.FuncFormatter(yAxisFormatter))
    axs[0].tick_params(axis='x', colors='white')
    axs[0].tick_params(axis='y', colors='white')
    for spine in axs[0].spines.values():
        spine.set_edgecolor('white')    

    # Call and Put Gamma Display
    axs[1].bar(strikes, dfAgg['CallGEX'].to_numpy(), width=0.2, linewidth=0.1, label="Call Gamma", color='green')
    axs[1].bar(strikes, dfAgg['PutGEX'].to_numpy(), width=0.2, linewidth=0.1, label="Put Gamma", color='red')
    axs[1].set_title("Gamma", color='white')
    axs[1].set_xlabel('Strike', color='white')
    axs[1].set_ylabel('Call and Put Gamma, $', color='white')
    axs[1].set_facecolor('black')
    axs[1].axhline(y=0, color='white', lw=0.5)
    axs[1].grid(True, linestyle='dashed', lw=0.3)
    axs[1].set_xlim([fromStrike, toStrike])
    axs[1].yaxis.set_major_formatter(ticker.FuncFormatter(yAxisFormatter))
    axs[1].legend()
    axs[1].tick_params(axis='x', colors='white')
    axs[1].tick_params(axis='y', colors='white')
    for spine in axs[1].spines.values():
        spine.set_edgecolor('white')
        
    # Call and Put Gamma Display
    colors = ['green' if value >= 0 else 'red' for value in dfAgg['TotalGamma'].to_numpy()]
    chartTitle = "Total Gamma: $" + str("{:.2f}".format(df['TotalGamma'].sum() / 10 ** 6)) + "M / 1% CVNA MOVE"
    xnew = np.linspace(strikes.min(), strikes.max(), 500)  # Smooth x values for interpolation
    spl = make_interp_spline(strikes, dfAgg['TotalGamma'].to_numpy(), k=5)
    ynew = spl(xnew)
    axs[2].plot(xnew, ynew, linewidth=1.5, label="Call Gamma", color='green')    #Plot Chart
    # axs[2].bar(strikes, dfAgg['TotalGamma'].to_numpy(), width=0.2, linewidth=0.1, label="Call Gamma", color=colors)  #Bar Chart
    # axs[2].plot(strikes, dfAgg['TotalGamma'].to_numpy(), linewidth=1, label="Call Gamma", color='green')    #Plot Chart
    axs[2].set_title(chartTitle, color='white')
    axs[2].set_xlabel('Strike', color='white')
    axs[2].set_ylabel('Total Gamma Exposure, $', color='white')
    axs[2].set_facecolor('black')
    axs[2].axhline(y=0, color='white', lw=0.5)
    axs[2].grid(True, linestyle='dashed', lw=0.3)
    axs[2].set_xlim([fromStrike, toStrike])
    axs[2].yaxis.set_major_formatter(ticker.FuncFormatter(yAxisFormatter))
    axs[2].tick_params(axis='x', colors='white')
    axs[2].tick_params(axis='y', colors='white')
    for spine in axs[2].spines.values():
        spine.set_edgecolor('white')    

    plt.tight_layout()
    plt.show()



# Use forward slashes in the file path
fileName = 'cvna_quotedata.csv'
downloadsFolder = os.path.expanduser('~/Downloads')
filePath = os.path.join(downloadsFolder, fileName).replace('/', '\\')
# delay(1, 3)

# This assumes the CBOE file format hasn't been edited, i.e. table beginds at line 4
optionsFile = open(filePath)
optionsFileData = optionsFile.readlines()
optionsFile.close()

# Get SPX Spot
spotLine = optionsFileData[1]
spotPrice = float(spotLine.split('Last:')[1].split(',')[0])
fromStrike = 0.5 * spotPrice
toStrike = 1.2 * spotPrice

# Get Today's Date
dateLine = optionsFileData[2]
todayDate = dateLine.split('Date: ')[1].split(',')
monthDay = todayDate[0].split(' ')
# Handling of US/EU date formats
if len(monthDay) == 2:
    year = int(todayDate[1].split()[0])
    month = monthDay[0]
    day = int(monthDay[1])
else:
    year = int(monthDay[2])
    month = monthDay[1]
    day = int(monthDay[0])

todayDate = datetime.strptime(month, '%B')
todayDate = todayDate.replace(day=day, year=year)

# Get SPX Options Data
df = pd.read_csv(filePath, sep=",", header=None, skiprows=4)
df.columns = ['ExpirationDate', 'Calls', 'CallLastSale', 'CallNet', 'CallBid', 'CallAsk', 'CallVol',
              'CallIV', 'CallDelta', 'CallGamma', 'CallOpenInt', 'StrikePrice', 'Puts', 'PutLastSale',
              'PutNet', 'PutBid', 'PutAsk', 'PutVol', 'PutIV', 'PutDelta', 'PutGamma', 'PutOpenInt']

df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'], format='%a %b %d %Y')
# df['ExpirationDate'] = df['ExpirationDate'] + timedelta(hours=16)
df['StrikePrice'] = df['StrikePrice'].astype(float)
df['CallIV'] = df['CallIV'].astype(float)
df['PutIV'] = df['PutIV'].astype(float)
df['CallGamma'] = df['CallGamma'].astype(float)
df['PutGamma'] = df['PutGamma'].astype(float)
df['CallOpenInt'] = df['CallOpenInt'].astype(float)
df['PutOpenInt'] = df['PutOpenInt'].astype(float)
print(df['ExpirationDate'])

# ---=== CALCULATE SPOT GAMMA ===---
# Gamma Exposure = Unit Gamma * Open Interest * Contract Size * Spot Price
# To further convert into 'per 1% move' quantity, multiply by 1% of spotPrice
df['CallGEX'] = df['CallGamma'] * df['CallOpenInt'] * 100 * spotPrice * spotPrice * 0.01
df['PutGEX'] = df['PutGamma'] * df['PutOpenInt'] * 100 * spotPrice * spotPrice * 0.01 * -1
df['TotalGamma'] = (df.CallGEX + df.PutGEX) 
df['Days'] = (df['ExpirationDate'] - todayDate).dt.days
df['Vanna'] = df['TotalGamma'] * df['Days']


# Define custom formatter function
def yAxisFormatter(y, pos):
    if -1000000 < y < 1000000:
        return f"{y/1000:.0f}K"
    else:
        return f"{y/1000000:.1f}M"

# UI components
selectedDateVar = StringVar(root)
selectedDateVar.set(df['ExpirationDate'].max().strftime('%Y-%m-%d'))
dateSelectBox = OptionMenu(root, selectedDateVar, * df['ExpirationDate'].dt.strftime('%Y-%m-%d').unique())
viewButton = Button(root, text="View", command=calculateAndDisplay)
dateSelectBox.grid(row=0, column=0, padx=10, pady=5)
viewButton.grid(row=0, column=1, padx=10, pady=5)



# # Start the tkinter main loop
root.mainloop()
calculateAndDisplay()