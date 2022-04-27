from xml.dom.minidom import Element
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List, Tuple
import pandas as pd
import time, sys
import numpy as np
from tqdm import tqdm

class EasyParse:
    def __init__(self) -> None:
        pass

    def sum(self, elements: list) -> float:
        data = np.array(self.trim(elements), dtype=np.float32)
        return np.sum(data)

    def trim(self, elements: list) -> list:
        data = []
        for e in elements:
            try:
                value = float(e.text.replace(',',''))
            except:
                value = 0
            finally:
                data.append(value)
        return data
    
    def to_float(self, text: str) -> float:
        if '%' in text:
            return float(text[:-1].replace(',','')) / 100
        else:
            try:
                return float(text.replace(',',''))
            except:
                return .0

class InvestingParser:
    def __init__(self) -> None:
        # Setting Chrome Driver
        chrome_options = Options()
        # chrome_options.add_argument('--headless') 
        chrome_options.add_argument(f'--window-size=1920,1080')
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
            )
        self.driver.implicitly_wait(30)

    def get(self, url:str) -> None:
        error_count = 0
        while True:
            try:
                self.driver.get(url)
            except:
                time.sleep(30)
                error_count += 1
                if error_count >= 100:
                    print('Time out')
                    sys.exit(1)
            else:
                break

    def parse_data(self, url:str,label:List, values:List) -> Tuple:
        ep = EasyParse()
        summary = np.zeros(len(label[0]))
        error_count = 0
        try:
            rows = self.driver.find_elements(
                by=By.XPATH,
                value=values[0]
            )
        except:
            self.get(url+'-financial-summary')
            error_count += 1
            if error_count >= 100:
                print('Time out')
                sys.exit(1)
        else:
            for row in rows:
                data = row.find_elements(
                    by=By.TAG_NAME,
                    value='td'
                )
                if data[0].text in label[0]:
                    summary[label[0].index(data[0].text)] = ep.sum(data[1:])
        percent = np.zeros(len(label[1]))
        error_count = 0
        try:
            rows = self.driver.find_elements(
                by=By.XPATH,
                value=values[1]
            )
        except:
            self.get(url+'-financial-summary')
            error_count += 1
            if error_count >= 100:
                print('Time out')
                sys.exit(1)
        else:
            for row in rows:
                spans = row.find_elements(
                    by=By.TAG_NAME,
                    value='span'
                )
                if spans[0].text in label[1]:
                    percent[label[1].index(spans[0].text)] = ep.to_float(spans[-1].text)
        return summary, percent

    def get_tickers(self) -> Dict:
        # Setting Chrome Driver
        self.get('https://www.investing.com/equities/united-states')
        # Change ticker list to S&P 500 from Dow Jones
        button = self.driver.find_element(
            by=By.XPATH, 
            value='//*[@id="166"]'
            )
        button.click()
        # Pasring ticker list
        error_count = 0
        while True:
            try:
                stock_list = WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'plusIconTd')))
            except:
                button.click()
                time.sleep(30)
                if error_count >= 100:
                    print('Time out')
                    sys.exit(1)
            else:
                break
        tickers = []
        for stock in tqdm(stock_list):
            info = stock.find_element(
                by=By.TAG_NAME, 
                value='a'
            )
            tickers.append([info.text, info.get_attribute('href').split('?')[0]])
        return tickers

    def get_fundamental(self, url:str) -> List:
        # Setting Chrome Driver
        self.get(url)
        # Overview Page
        overview = np.zeros(3, dtype=np.float32)
        error_count = 0
        while True:
            try:
                dl = WebDriverWait(self.driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'dl')))
            except:
                self.get(url)
                error_count += 1
                if error_count >= 100:
                    print('Time out')
                    sys.exit(1)
            else:
                dds = dl.find_elements(
                   by=By.TAG_NAME,
                    value='dd'
                )
                break
        low, high = dds[4].text.split('-')
        overview[0] = float(low.replace(',', '')) # 52wk lowest price
        overview[1] = float(high.replace(',', '')) # 52wk highest price
        overview[2] = float(dds[13].text.replace(',', '')) # Outstanding
        # Financial Summary Page
        self.get(url+'-financial-summary')
        # Income Statement
        label = [
            ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income'],
            ['Gross margin', 'Operating margin', 'Net Profit margin', 'Return on Investment']    
        ]
        values = ['//*[@id="rsdiv"]/div[1]/table/tbody/tr', '//*[@id="rsdiv"]/div[1]/div[1]/div']
        income_summary, income_percent = self.parse_data(url, label, values)
        # Balance Sheet
        label = [
            ['Total Assets', 'Total Liabilities', 'Total Equity'],
            ['Quick Ratio', 'Current Ratio', 'LT Debt to Equity', 'Total Debt to Equity']
        ]
        values = ['//*[@id="rsdiv"]/div[3]/table/tbody/tr', '//*[@id="rsdiv"]/div[3]/div[1]/div']
        balance_summary, balance_percent = self.parse_data(url, label, values)
        # Cash Flow Statement
        label = [
            ['Cash From Operating Activities', 'Cash From Investing Activities', 'Cash From Financing Activities', 'Net Change in Cash'],
            ['Cash Flow/Share', 'Revenue/Share', 'Operating Cash Flow']
        ]
        values = ['//*[@id="rsdiv"]/div[5]/table/tbody/tr', '//*[@id="rsdiv"]/div[5]/div[1]/div']
        cash_summary, cash_percent = self.parse_data(url, label, values)
        fundamental = np.concatenate((overview, income_summary, income_percent, balance_summary, balance_percent, cash_summary, cash_percent), axis=None)
        return fundamental

    def run(self) -> None:
        try: 
            # Read Ticker list from data/
            ticker_list = pd.read_csv('./data/ticker_list.csv', index_col=0)
        except:
            # Parse Ticker list from investing.com
            tickers = self.get_tickers()
            # Save Ticker list to data/
            ticker_list = pd.DataFrame(data=tickers, columns=['Co.', 'URL'])
            ticker_list = ticker_list.set_index(['Co.'])
            ticker_list.sort_index(inplace=True)
            ticker_list.to_csv('./data/ticker_list.csv')
        # Parse ticker's fundamental from each investing.com page
        columns = ['Low Price', 'High Price', 'Outstanding', 
                  'Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income',
                  'Gross margin', 'Operating margin', 'Net Profit margin', 'Return on Investment',
                  'Total Assets', 'Total Liabilities', 'Total Equity',
                  'Quick Ratio', 'Current Ratio', 'LT Debt to Equity', 'Total Debt to Equity',
                  'Cash From Operating Activities', 'Cash From Investing Activities', 'Cash From Financing Activities', 'Net Change in Cash',
                  'Cash Flow/Share', 'Revenue/Share', 'Operating Cash Flow']
        data = []
        for ticker in tqdm(ticker_list.index):
            fundamental = self.get_fundamental(ticker_list.loc[ticker]['URL'])
            data.append(fundamental)
        self.driver.quit()
        ticker_fund = pd.DataFrame(data=data, columns=columns, index=ticker_list.index)
        ticker_fund.to_csv('./data/fundamentals.csv')
        return

if __name__ == '__main__':
    p = InvestingParser()
    p.run()