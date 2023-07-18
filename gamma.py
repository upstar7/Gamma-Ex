import pandas as pd
import numpy as np
import scipy
from scipy.stats import norm
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date

pd.options.display.float_format = '{:,.4f}'.format

# Inputs and Parameters
# filename = 'cvna_quotedata.csv'
filename = 'cvna_quotedata_July.csv'

# Black-Scholes European-Options Gamma
def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    if T == 0 or vol == 0:
        return 0

    dp = (np.log(S/K) + (r - q + 0.5*vol**2)*T) / (vol*np.sqrt(T))
    dm = dp - vol*np.sqrt(T) 

    if optType == 'call':
        gamma = np.exp(-q*T) * norm.pdf(dp) / (S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma 
    else: # Gamma is same for calls and puts. This is just to cross-check
        gamma = K * np.exp(-r*T) * norm.pdf(dm) / (S * S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma 

def isThirdFriday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21

# This assumes the CBOE file format hasn't been edited, i.e. table beginds at line 4
optionsFile = open(filename)
optionsFileData = optionsFile.readlines()
optionsFile.close()

# Get SPX Spot
spotLine = optionsFileData[1]
spotPrice = float(spotLine.split('Last:')[1].split(',')[0])
fromStrike = 0.5 * spotPrice
toStrike = 1.5 * spotPrice

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

todayDate = datetime.strptime(month,'%B')
todayDate = todayDate.replace(day=day, year=year)

# Get SPX Options Data
df = pd.read_csv(filename, sep=",", header=None, skiprows=4)
df.columns = ['ExpirationDate','Calls','CallLastSale','CallNet','CallBid','CallAsk','CallVol',
              'CallIV','CallDelta','CallGamma','CallOpenInt','StrikePrice','Puts','PutLastSale',
              'PutNet','PutBid','PutAsk','PutVol','PutIV','PutDelta','PutGamma','PutOpenInt']

df['ExpirationDate'] = pd.to_datetime(df['ExpirationDate'], format='%a %b %d %Y')
df['ExpirationDate'] = df['ExpirationDate'] + timedelta(hours=16)
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
df['TotalGamma'] = (df.CallGEX + df.PutGEX) / 10 ** 6
dfAgg = df.groupby(['StrikePrice'])[['CallGEX', 'PutGEX', 'TotalGamma']].sum()
strikes = dfAgg.index.values

# Display Gamma Exposure
fig = plt.figure()
fig.set_facecolor('black')
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['axes.edgecolor'] = 'white'
plt.grid(True, linestyle='dashed', lw=0.3)
colors = ['green' if value >= 0 else 'red' for value in dfAgg['TotalGamma'].to_numpy()]
plt.bar(strikes, dfAgg['TotalGamma'].to_numpy(), width=0.2, linewidth=0.1, label="Gamma Exposure", color=colors)
plt.gca().set_facecolor('black')
plt.rcParams['axes.edgecolor'] = 'white'
plt.xlim([fromStrike, toStrike])
chartTitle = "Total Gamma: $" + str("{:.2f}".format(df['TotalGamma'].sum())) + " M per 1% CVNA Move"
plt.title(chartTitle, fontweight="bold", fontsize=20, color='white')
plt.xlabel('Strike', fontweight="bold", color='white')
plt.ylabel('Spot Gamma Exposure ($M / 1% move)', fontweight="bold", color='white')
plt.axhline(y=0, color='white', lw=0.5)
plt.legend()
plt.show()

