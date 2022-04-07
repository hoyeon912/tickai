from pandas import DataFrame
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Dict, Tuple, List

class Parser:
    def __init__(self) -> None:
        WINDOW_SIZE = '1920,1080'

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument(f'--window-size={WINDOW_SIZE}')

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
            )
        self.driver.implicitly_wait(3)
        self.driver.get('https://www.investing.com/equities/united-states')

    def get_tickers(self) -> Dict:
        print('Get Ticker List from investing.com')
        button = self.driver.find_element(
            by=By.XPATH, 
            value='//*[@id="all"]'
            )
        button.click()
        time.sleep(10)

        stock_list = self.driver.find_elements(
            by=By.CLASS_NAME, 
            value='plusIconTd'
        )

        filtered_dict = {}
        for stock in stock_list:
            info = stock.find_element(
                by=By.TAG_NAME, 
                value='a'
            )
            filtered_dict[info.text] = info.get_attribute('href')
        return filtered_dict

    def get_url(self, stock_url: str) -> Tuple[str,]:
        income = f'{stock_url}-income-statement'
        balance = f'{stock_url}-balance-sheet'
        cash = f'{stock_url}-cash-flow'
        return stock_url, income, balance, cash

    def get_item(self, xpath: str) -> int:
        row = self.driver.find_element(
            by=By.XPATH,
            value=xpath
        )
        elements = row.find_elements(
            by=By.TAG_NAME,
            value='td'
        )
        sum = 0
        for element in elements[1:]:
            if element.text == '-':
                element = 0
            sum += int(element.text)
        return sum

    def get_info(self, urls: List) -> List[str,]:
        result = []

        print('--- parsing summary page')
        self.driver.get(urls[0])
        result.append(int(self.driver.find_element(
            by=By.XPATH,
            value='//*[@id="__next"]/div[2]/div/div/div[2]/main/div/div[1]/div[2]/ul/li[1]/div[2]'
        ).text.replace(',', '')))
        low, _, high = self.driver.find_element(
            by=By.XPATH,
            value='//*[@id="__next"]/div[2]/div/div/div[2]/main/div/div[1]/div[2]/ul/li[3]/div[2]'
        ).text.replace(',', '').split(' ')
        result.append(float(low))
        result.append(float(high))

        print('--- parsing income page')
        self.driver.get(urls[1])
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[1]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[3]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[5]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[19]'))

        print('--- parsing balance page')
        self.driver.get(urls[2])
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[1]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[2]/td/div/table/tbody/tr[1]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[2]/td/div/table/tbody/tr[5]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[2]/td/div/table/tbody/tr[7]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[3]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[3]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[5]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[7]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[8]/td/div/table/tbody/tr[1]'))

        print('--- parsing cash flow page')
        self.driver.get(urls[3])
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[2]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[2]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[4]'))
        result.append(self.get_item('/html/body/div[5]/section/div[9]/table/tbody[2]/tr[6]'))

        return result

    def run(self) -> DataFrame:
        print('\n===== Investing.com Parser ======')
        tickers = self.get_tickers()
        print(f'Total number of tickers is {len(tickers)}')
        
        index = tickers.keys()
        columns = ['Volume', 'Low Price', 'High Price',
                  'Revenue', 'Cost of Revenue', 'Operating Expense',
                  'Net Income', 'Current Asset', 'Cash Investment',
                  'Receivables', 'Inventory', 'Asset', 'Fixed Asset',
                  'Current Liabilities', 'Liabilities', 'Long Term Debt']
        data = []
        
        print("Get each ticker's infomation.")
        for ticker in index:
            print(f"{ticker} page is parsed.")
            urls = self.get_url(tickers[ticker])
            data.append(self.get_info(urls))
        df = DataFrame(data=data, index=index, columns=columns)

        return df
        
if __name__ == '__main__':
    p = Parser()
    p.run().to_csv('../data/ticker_info.csv')