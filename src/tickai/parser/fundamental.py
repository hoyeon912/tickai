from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import investpy
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import pandas as pd
import time
import pickle

class Dict(dict):
    @property
    def length(self):
        if self:
            return len(self[list(self.keys())[0]])
        else:
            return 0

    def copy(self):
        return Dict(self)

    def concatenate(self, src):
        dist = self.copy()
        keys = set(self.keys()) | set(src.keys())
        for key in keys:
            if key in self.keys() and key in src.keys(): 
                dist[key] = dist[key] + [src[key]]
            elif key in self.keys() and key not in src.keys(): 
                dist[key] = dist[key] + [0]
            else: 
                dist[key] = [0 for _ in range(self.length)] + [src[key]]
        return Dict(dist)

def _get_text(element):
    return element.text

def _get_date(text):
    try:
        year, daymonth = text.split('\n')
    except:
        print(text)
    return daymonth + '/' + year

def _get_value(text):
    try:
        return float(text)
    except:
        return 0

def _put_table(element, dics):
    trs = element.find_elements(
        by=By.TAG_NAME,
        value='tr'
    )
    trs_with_noHober = element.find_elements(
        by=By.CLASS_NAME,
        value='noHover'
    )
    trs_without_noHober = set(trs) - set(trs_with_noHober)
    for tr in trs_without_noHober:
        tds = tr.find_elements(
            by=By.TAG_NAME,
            value='td'
        )
        data = list(map(_get_text, tds))
        key = data[0]
        for e in enumerate(list(map(_get_value, data[1:]))):
            i, value = e
            dics[i][key] = value
    return dics

def _get_period(element):
    ths = element.find_elements(
        by=By.TAG_NAME,
        value='th'
    )
    starts = []
    ends = []
    for date in list(map(_get_date, map(_get_text, ths[1:5]))):
        end = datetime.strptime(date, '%d/%m/%Y')
        start = end - relativedelta(years=1) 
        start += relativedelta(days=7-start.weekday())
        starts.append(start.strftime('%d/%m/%Y'))
        ends.append(end.strftime('%d/%m/%Y'))
    return starts, ends

def _put_summary(search_obj, period, dics):
    starts, ends = _get_period(period)
    for e in enumerate(zip(starts, ends)): # Lastest to Oldest!
        i, (start, end) = e
        while True:
            try:
                df = search_obj.retrieve_historical_data(from_date=start, to_date=end)
            except IndexError:
                return i, True
            except:
                time.sleep(5)
            else:
                break
        dics[i]['High'] = df['High'].max()
        dics[i]['Low'] = df['Low'].min()
        dics[i]['avg Volume'] = df['Volume'].mean()
    return i, False

def _get(name, url, driver):
    pages = ['-income-statement', '-balance-sheet', '-cash-flow']
    dics = [Dict() for _ in range(4)]
    for page in pages:
        driver.get(url+page)
        while True:
            try:
                btn = driver.find_element(
                    by=By.XPATH,
                    value='//*[@id="leftColumn"]/div[8]/div[1]/a[1]'
                )
                driver.execute_script('arguments[0].click();', btn)
                period, data = driver.find_elements(
                    by=By.XPATH,
                    value='//*[@id="rrtable"]/table/tbody'
                )
            except:
                driver.refresh()
            else:
                break
        _put_table(data, dics)
    search_obj = investpy.search_quotes(name, ['stocks'], ['united states'], n_results=1)
    i, err = _put_summary(search_obj, period, dics)
    return dics[:i] if err else dics

def get(driver):
    stocks = pd.read_csv('./data/stocklist.csv', index_col=0)
    train_ds = Dict({})
    test_ds = Dict({})
    for stock in tqdm(stocks.index):
        dics = _get(stock, stocks.loc[stock]['URL'], driver)
        test_ds = test_ds.concatenate(dics[0])
        for dic in dics[1:]:
                train_ds = train_ds.concatenate(dic)
        time.sleep(5)
    # TODO : Change to abstract address
    with open('./data/train_ds.pickle', 'wb') as f:
        try:
            pickle.dump(train_ds, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as ex:
            print(f'Error during pickling: {ex}')
    with open('./data/test_ds.pickle', 'wb') as f:
        try:
            pickle.dump(train_ds, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as ex:
            print(f'Error during pickling: {ex}')
    train_df = pd.DataFrame.from_dict(train_ds)
    train_df.to_csv('./data/train_ds.csv')
    test_df = pd.DataFrame.from_dict(test_ds)
    test_df.to_csv('./data/test_ds.csv')