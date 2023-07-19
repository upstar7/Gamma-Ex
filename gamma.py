import pandas as pd
import numpy as np
import scipy
from scipy.stats import norm
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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

filePath = os.path.expanduser('~/Downloads/cvna_quotedata.csv')

if os.path.exists(filePath):
    os.remove(filePath)

def delay(s, e):
    interval = random.uniform(s, e)
    time.sleep(interval)

def initialize_driver():
    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
    chromeOptions = uc.ChromeOptions()
    chromeOptions.add_argument(f'user-agent={useragent}')
    # chromeOptions.headless = True
    # chromeOptions.add_argument("--headless")

    chromeOptions.add_argument("--disable-blink-features=AutomationControlled")
    chromeOptions.add_argument("--no-first-run")
    chromeOptions.add_argument("--no-service-autorun")
    chromeOptions.add_argument("--no-default-browser-check")
    chromeOptions.add_argument("--disable-extensions")
    chromeOptions.add_argument("--disable-popup-blocking")
    chromeOptions.add_argument("--profile-directory=Default")
    chromeOptions.add_argument("--ignore-certificate-errors")
    chromeOptions.add_argument("--disable-plugins-discovery")
    chromeOptions.add_argument("--incognito")
    chromeOptions.add_argument("--start-maximized")
    chromeOptions.add_argument('--no-sandbox')

    global driver
    driver = uc.Chrome(executable_path=ChromeDriverManager().install(), options=chromeOptions)


initialize_driver()

# Navigate to the webpage
driver.get('https://www.cboe.com/delayed_quotes/cvna/quote_table')

try:
    delay(1, 3)
    driver.find_element(By.CSS_SELECTOR, ".button--solid.privacy-alert__agree-button").click()
except:
    pass

try:
    delay(1, 3)
    optionRange = driver.find_element(By.CSS_SELECTOR, '#root > div > div > div.Box-sc-jzm6b1-0.cvqwTQ > div.Box-sc-jzm6b1-0.Tabs___StyledBox-sc-zx70g3-6.jkMlqj > div:nth-child(2) > div.Box-sc-jzm6b1-0.Flex-sc-9zr7dk-0.cXQocl > div:nth-child(3) > div > div.Box-sc-jzm6b1-0.FormField__Field-sc-150d642-0.dTWjar > div > div > div')
    optionRange.click()
except:
    pass

try:
    delay(1, 3)
    optionRangeAll = driver.find_element(By.CSS_SELECTOR, '.ReactSelect__menu > div > div:nth-child(1)')
    optionRangeAll.click()
except:
    pass

try:
    delay(1, 3)
    viewChainButton = driver.find_element(By.CSS_SELECTOR, '.Button__StyledButton-sc-1tdgwi0-2.gNcAGf')
    viewChainButton.click()
except:
    pass

try:
    delay(1, 3)
    downloadButton = driver.find_element(By.CSS_SELECTOR, '.Button__StyledButton-sc-1tdgwi0-2.kvidqt')
    downloadButton.click()
except:
    pass


pd.options.display.float_format = '{:,.4f}'.format


# Black-Scholes European-Options Gamma

def calcGammaEx(S, K, vol, T, r, q, optType, OI):
    if T == 0 or vol == 0:
        return 0

    dp = (np.log(S/K) + (r - q + 0.5*vol**2)*T) / (vol*np.sqrt(T))
    dm = dp - vol*np.sqrt(T)

    if optType == 'call':
        gamma = np.exp(-q*T) * norm.pdf(dp) / (S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma
    else:  # Gamma is same for calls and puts. This is just to cross-check
        gamma = K * np.exp(-r*T) * norm.pdf(dm) / (S * S * vol * np.sqrt(T))
        return OI * 100 * S * S * 0.01 * gamma


def isThirdFriday(d):
    return d.weekday() == 4 and 15 <= d.day <= 21

# Use forward slashes in the file path
fileName = 'cvna_quotedata.csv'
downloadsFolder = os.path.expanduser('~/Downloads')
filePath = os.path.join(downloadsFolder, fileName).replace('/', '\\')
delay(1, 3)

# This assumes the CBOE file format hasn't been edited, i.e. table beginds at line 4
optionsFile = open(filePath)
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

todayDate = datetime.strptime(month, '%B')
todayDate = todayDate.replace(day=day, year=year)

# Get SPX Options Data
df = pd.read_csv(filePath, sep=",", header=None, skiprows=4)
df.columns = ['ExpirationDate', 'Calls', 'CallLastSale', 'CallNet', 'CallBid', 'CallAsk', 'CallVol',
              'CallIV', 'CallDelta', 'CallGamma', 'CallOpenInt', 'StrikePrice', 'Puts', 'PutLastSale',
              'PutNet', 'PutBid', 'PutAsk', 'PutVol', 'PutIV', 'PutDelta', 'PutGamma', 'PutOpenInt']

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
df['TotalGamma'] = (df.CallGEX + df.PutGEX) 
dfAgg = df.groupby(['StrikePrice'])[['CallGEX', 'PutGEX', 'TotalGamma']].sum()
strikes = dfAgg.index.values

# Display Gamma Exposure
fig = plt.figure()
fig.set_facecolor('black')
colors = ['blue' if value >= 0 else 'red' for value in dfAgg['TotalGamma'].to_numpy()]
chartTitle = "Total Gamma: $" + str("{:.2f}".format(df['TotalGamma'].sum() / 10 ** 6)) + "M per 1% CVNA Move"
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['axes.edgecolor'] = 'white'
plt.rcParams['axes.edgecolor'] = 'white'
plt.grid(True, linestyle='dashed', lw=0.3)
plt.bar(strikes, dfAgg['TotalGamma'].to_numpy(), width=0.2, linewidth=0.1, label="Gamma Exposure", color=colors)
plt.gca().set_facecolor('black')
plt.xlim([fromStrike, toStrike])
plt.title(chartTitle, fontweight="bold", fontsize=20, color='white')
plt.xlabel('Strike', fontweight="bold", color='white')
plt.ylabel('Spot Gamma Exposure ($ / 1% move)', fontweight="bold", color='white')
plt.axhline(y=0, color='white', lw=0.5)
plt.legend()

# Define custom formatter function
def yAxisFormatter(y, pos):
    if y >= 1000000:
        return f"{y/1000000:.1f}M"
    else:
        return f"{y/1000:.0f}K"

# Apply formatter to the y-axis tick labels
plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(yAxisFormatter))

plt.show()
