from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List
import pandas as pd
from tqdm import tqdm

class Parser:
    def __init__(self) -> None:
        # Setting Webdriver option
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument(f'--window-size=1920, 1080')
        # Load Chrome driver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
            )
        self.driver.implicitly_wait(10)
        self.driver.get('https://www.investing.com/equities/united-states')

    def get_tickers(self) -> Dict:
        # Change ticker list to S&P 500 from Dow Jones
        button = self.driver.find_element(
            by=By.XPATH, 
            value='//*[@id="166"]'
            )
        button.click()
        # Pasring ticker list
        stock_list = WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'plusIconTd')))
        tickers = []
        for stock in tqdm(stock_list):
            info = stock.find_element(
                by=By.TAG_NAME, 
                value='a'
            )
            tickers.append([info.text, info.get_attribute('href')])
        return tickers

    def get_fundamental(self, url:str) -> List:
        fundamental = []
        # Overview Page
        self.driver.get(url)
        dl = WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'dl')))
        dds = dl.find_elements(
            by=By.TAG_NAME,
            value='dd'
        )
        low, high = dds[4].text.split('-')
        fundamental.append(float(low)) # 52wk lowest price
        fundamental.append(float(high)) # 52wk highest price
        fundamental.append(int(dds[13].text.replace(',', ''))) # Outstanding
        # Financial Summary Page
        self.driver.get(url+'-financial-summary')
        return fundamental

    def run(self) -> None:
        print('\n===== Investing.com Parser ======')
        # Parse Ticker list from investing.com
        print('Get Ticker List from investing.com')
        tickers = self.get_tickers()
        # Save Ticker list to data/
        print('Save Ticker List')
        df = pd.DataFrame(data=tickers, columns=['Co.', 'URL'])
        df = df.set_index(['Co.'])
        df.to_csv('./data/ticker_list.csv')
        # Read Ticker list from data/
        # maybe this is not essential
        print('Read Ticker List')
        df = pd.read_csv('./data/ticker_list.csv', index_col=0)
        print(f'Total number of tickers is {len(df.index)}')
        # Parse ticker's fundamental from each investing.com page
        print("Get each ticker's infomation.")
        columns = ['Low Price', 'High Price', 'Outstanding', 
                  'Revenue', 'Cost of Revenue', 'Operating Expense',
                  'Net Income', 'Current Asset', 'Cash Investment',
                  'Receivables', 'Inventory', 'Asset', 'Fixed Asset',
                  'Current Liabilities', 'Liabilities', 'Long Term Debt']
        data = []
        for ticker in tqdm(df.index):
            fundamental = self.get_fundamental(df.loc[ticker]['URL'])
            data.append(fundamental)
        df_fund = pd.DataFrame(data=data, columns=columns, index=df.index)
        df_fund.to_csv('./data/fundamentals.csv')
        return
        
if __name__ == '__main__':
    p = Parser()
    p.run()