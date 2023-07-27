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
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


pd.options.display.float_format = '{:,.4f}'.format

def on_option_change(value):
    # Function to handle the OptionMenu selection change
    pass

def on_button_click():
    # Function to handle the "View" button click
    calculateAndDisplay()

def calculateAndDisplay():
    
    # Create three subplots within one figure
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Vanna/Gamma Exposure Visualization", fontsize=16)
    fig.set_facecolor('black')
    
    root = Tk()
    root.title("Gamma Exposure Visualization")
   
   # Add the select box for expiration date
    selectedDateVar = StringVar(root)
    expiration_dates = sorted(df['ExpirationDate'].dt.strftime('%Y-%m-%d').unique())
    print(expiration_dates)
    selectedDateVar.set(expiration_dates[0])
    select_date = OptionMenu(root, selectedDateVar, *expiration_dates, command=on_option_change)
    select_date.config(bg='white', font=('Arial', 10))

    # Add the "View" button
    view_button = Button(root, text='View', bg='white', activebackground='yellow', command=on_button_click)
    view_button.pack()
    
    selectedDate = datetime.strptime(selectedDateVar.get(), '%Y-%m-%d')
    
    # Add the selected expiration date as a text annotation
    expirationDateText = selectedDate.strftime('%Y-%m-%d') 
    fig.text(0.5, 0.98, f"Expiration Date: {expirationDateText}", ha='center', va='top', color='yellow', fontsize=16)
    
    # Filter data based on selected expiration date
    filteredDf = df[df['ExpirationDate'] == selectedDate]
    dfAgg = filteredDf.groupby(['StrikePrice'])[['Vanna', 'CallGEX', 'PutGEX', 'TotalGamma']].sum()
    strikes = dfAgg.index.values
    

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
    axs[1].legend(loc='upper left')
    axs[1].tick_params(axis='x', colors='white')
    axs[1].tick_params(axis='y', colors='white')
    for spine in axs[1].spines.values():
        spine.set_edgecolor('white')
        
    # Call and Put Gamma Display
    chartTitle = "Total Gamma: $" + str("{:.2f}".format(df['TotalGamma'].sum() / 10 ** 6)) + "M / 1% CVNA MOVE"
    xnew = np.linspace(strikes.min(), strikes.max(), 500)  # Smooth x values for interpolation
    spl = make_interp_spline(strikes, dfAgg['TotalGamma'].to_numpy(), k=5)
    ynew = spl(xnew)
    axs[2].plot(xnew, ynew, linewidth=1.5, label="Call Gamma", color='green')    #Plot Chart
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
    # plt.show()

    # Add the plot to the tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()

    # Add the NavigationToolbar to the tkinter window
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()

    # Position the plot and toolbar in the tkinter window
    canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
    toolbar.pack(side='top', fill='both', padx=5, pady=5)

    # Start the tkinter main loop
    root.mainloop()
    
    
     
    # Calculate max and min values for each plot
    maxVanna = dfAgg['Vanna'].max()
    minVanna = dfAgg['Vanna'].min()
    maxGamma = dfAgg['CallGEX'].max()
    minGamma = dfAgg['PutGEX'].min()
    maxGammaExposure = dfAgg['TotalGamma'].max()
    minGammaExposure = dfAgg['TotalGamma'].min()
    
    # Add text annotations for max and min values to each plot
    axs[0].text(0.98, 0.95, f"Max: {maxVanna:.2f}", ha='right', va='top', transform=axs[0].transAxes, color='green')
    axs[0].text(0.98, 0.90, f"Min: {minVanna:.2f}", ha='right', va='top', transform=axs[0].transAxes, color='red')
    axs[1].text(0.98, 0.95, f"Max: {maxGamma:.2f}", ha='right', va='top', transform=axs[1].transAxes, color='green')
    axs[1].text(0.98, 0.90, f"Min: {minGamma:.2f}", ha='right', va='top', transform=axs[1].transAxes, color='red')
    axs[2].text(0.98, 0.95, f"Max: {maxGammaExposure:.2f}", ha='right', va='top', transform=axs[2].transAxes, color='green')
    axs[2].text(0.98, 0.90, f"Min: {minGammaExposure:.2f}", ha='right', va='top', transform=axs[2].transAxes, color='red')

   


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

# Ensure this block of code is executed only when this script is run
if __name__ == "__main__":
    calculateAndDisplay()