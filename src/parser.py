# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
# Type Annotation
from typing import Dict, List
# Data Visulization
import pandas as pd

class EasyParse:
    def __init__(self) -> None:
        pass

    def sum_items(self, elements) -> float:
        sum = 0
        for e in elements[1:]:
            try:
                sum += float(e.text.replace(',',''))
            except:
                continue
        return sum

    def rm_percent(self, element) -> float:
        value = element.text.replace(',','').split('%')[0]
        try:
            value = float(value)
        except:
            value = 0
        return value

class InvestingParser:
    def __init__(self) -> None:
        # Setting Chrome Driver
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless') 
        self.chrome_options.add_argument(f'--window-size=1920, 1080')
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.chrome_options
            )
        self.driver.implicitly_wait(30)

    def get_tickers(self) -> Dict:
        # Setting Chrome Driver
        self.driver.get('https://www.investing.com/equities/united-states')
        # Change ticker list to S&P 500 from Dow Jones
        button = self.driver.find_element(
            by=By.XPATH, 
            value='//*[@id="166"]'
            )
        button.click()
        # Pasring ticker list
        stock_list = WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'plusIconTd')))
        tickers = []
        for stock in stock_list:
            info = stock.find_element(
                by=By.TAG_NAME, 
                value='a'
            )
            tickers.append([info.text, info.get_attribute('href')])
        return tickers

    def get_fundamental(self, url:str) -> List:
        # Setting Chrome Driver
        self.driver.get(url)
        # Overview Page
        fundamental = []
        dl = WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'dl')))
        dds = dl.find_elements(
            by=By.TAG_NAME,
            value='dd'
        )
        low, high = dds[4].text.split('-')
        fundamental.append(float(low.replace(',', ''))) # 52wk lowest price
        fundamental.append(float(high.replace(',', ''))) # 52wk highest price
        fundamental.append(int(dds[13].text.replace(',', ''))) # Outstanding
        # Financial Summary Page
        self.driver.get(url+'-financial-summary')
        ep = EasyParse()
        # Total Revenue
        fundamental.append(ep.sum_items(self.driver.find_elements(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[1]/table/tbody/tr[1]'
        )))
        # Net Profit Margin
        fundamental.append(ep.rm_percent(self.driver.find_element(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[1]/div[1]/div[3]/span[3]'
        )))
        # Total Liabilities
        fundamental.append(ep.sum_items(self.driver.find_elements(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[3]/table/tbody/tr[2]'
        )))
        # Total Equity
        fundamental.append(ep.sum_items(self.driver.find_elements(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[3]/table/tbody/tr[3]'
        )))
        # LT Debt to Equity
        fundamental.append(ep.rm_percent(self.driver.find_element(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[3]/div[1]/div[3]/span[3]'
        )))
        # Total Debt to Equity
        fundamental.append(ep.rm_percent(self.driver.find_element(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[3]/div[1]/div[4]/span[3]'
        )))
        # Cash From Investing Activities
        fundamental.append(ep.sum_items(self.driver.find_elements(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[5]/table/tbody/tr[2]'
        )))
        # Cash From Financing Activities
        fundamental.append(ep.sum_items(self.driver.find_elements(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[5]/table/tbody/tr[3]'
        )))
        # Net Change in Cash
        fundamental.append(ep.sum_items(self.driver.find_elements(
            by=By.XPATH,
            value='/html/body/div[5]/section/div[12]/div[5]/table/tbody/tr[4]'
        )))
        return fundamental

    def run(self) -> None:
        try:
            # Read Ticker list from data/
            ticker_list = pd.read_csv('./data/ficker_list.csv', index_col=0)
        except:
            # Parse Ticker list from investing.com
            tickers = self.get_tickers()
            # Save Ticker list to data/
            ticker_list = pd.DataFrame(data=tickers, columns=['Co.', 'URL'])
            ticker_list = ticker.set_index(['Co.'])
            ticker_list.to_csv('./data/ticker_list.csv')
        # Parse ticker's fundamental from each investing.com page
        columns = ['Low Price', 'High Price', 'Outstanding', 
                  'Total Revenue', 'Net Profit margin',
                  'Total Liabilities', 'Total Equity', 'LT Debt to Equity', 'Total Debt to Equity',
                  'Cash From Investing Activities', 'Cash From Financing Activities', 'Net Change in Cash']
        data = []
        for ticker in ticker_list.index:
            fundamental = self.get_fundamental(ticker_list.loc[ticker]['URL'])
            data.append(fundamental)
        ticker_fund = pd.DataFrame(data=data, columns=columns, index=ticker_list.index)
        ticker_fund.to_csv('./data/fundamentals.csv')
        return
        
if __name__ == '__main__':
    p = InvestingParser()
    p.run()