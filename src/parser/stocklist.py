from pyparsing import col
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import pandas as pd

chrome_options = Options()
chrome_options.headless = True
chrome_options.add_argument('--disable-logging')
chrome_options.add_argument('--disable-in-process-stack-traces')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
driver.implicitly_wait(30)

url = 'https://www.investing.com/equities/united-states'
driver.get(url)

button = driver.find_element(
    by=By.XPATH, 
    value='//*[@id="166"]'
)
button.click()

stock_list = WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'plusIconTd')))
data = {}
for stock in tqdm(stock_list):
    info = stock.find_element(
        by=By.TAG_NAME,
        value='a'
    )
    data[info.text] = info.get_attribute('href').split('?')[0]

df = pd.DataFrame.from_dict(data, orient='index', columns=['URL'])
df = df.sort_index()
df.to_csv('./data/stocklist.csv')

driver.quit()