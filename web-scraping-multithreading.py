from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import threading
from multiprocessing.pool import ThreadPool, Pool

logsFileName = "logs.txt"
threadLocal = threading.local()

def convert_to_int(string):
    # Replace various hyphen characters with a standard minus sign and remove commas
    string = string.replace('–', '-').replace('−', '-').replace('—', '-').replace(',', '')
    try:
        # Handle 'k' for thousands
        if 'k' in string:
            number = float(string[:-1]) * 1000
        else:
            number = float(string)
        return int(number)
    except ValueError as e:
        print(f"Error converting '{string}' to int: {e}")
        return 0

def getPageLinks(url_prefix, start, stop, step):
    links = []
    for i in range(start, stop, step):
        links.append(url_prefix + str(i))
    return links

def getDriver():
    driver = getattr(threadLocal, 'driver', None)
    if driver is None:
        chromeOptions = webdriver.ChromeOptions()
        # chromeOptions.add_argument("--headless")
        driver = webdriver.Chrome(options=chromeOptions)
        setattr(threadLocal, 'driver', driver)
    return driver

def parseAndSaveOnePage(page_url):
    page_data = []
    driver = getDriver()
    driver.get(page_url)
    json_filename = "data/" + str(page_url.split("start=")[1]).zfill(8) + ".json"
    wait = WebDriverWait(driver, 2)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.qa-body-wrapper > div > div.qa-main > div.qa-main-heading')))

        parent_element = driver.find_element(By.CSS_SELECTOR, "body > div.qa-body-wrapper > div > div.qa-main > div.qa-part-q-list > form > div.qa-q-list.qa-q-list-vote-disabled")
        items = parent_element.find_elements(By.CSS_SELECTOR, "div.qa-q-list-item")
        
        for i in range(len(items)):
            # Заново находим элементы, чтобы избежать StaleElementReferenceException
            parent_element = driver.find_element(By.CSS_SELECTOR, "body > div.qa-body-wrapper > div > div.qa-main > div.qa-part-q-list > form > div.qa-q-list.qa-q-list-vote-disabled")
            items = parent_element.find_elements(By.CSS_SELECTOR, "div.qa-q-list-item")
            
            item = items[i]
            question_link = item.find_element(By.CSS_SELECTOR, 'div.qa-q-item-main > div > div.qa-q-item-title > a')
            
            # Сохраняем URL вопроса и переходим по ссылке
            question_href = question_link.get_attribute("href")
            driver.get(question_href)
            
            try:
                # Ожидание загрузки страницы с вопросом
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > div.qa-body-wrapper > div > div.qa-main > div.qa-main-heading')))
                
                question_title_element = driver.find_element(By.CSS_SELECTOR, '.qa-main-heading > h1 > a > span')
                question_title = question_title_element.text.strip()

                question_content_element = driver.find_element(By.CSS_SELECTOR, '.qa-q-view-content.qa-post-content')
                question_content = question_content_element.text.strip()

                date_element = driver.find_element(By.CSS_SELECTOR, '.qa-q-view-when > span')
                question_date = date_element.text.strip()

                category_element = driver.find_element(By.CSS_SELECTOR, '.qa-q-view-where > span > a')
                category_text = category_element.text.strip()

                view_element = driver.find_element(By.CSS_SELECTOR, '.qa-view-count-data')
                view_count = view_element.text.strip()

                upvote_element = driver.find_element(By.CSS_SELECTOR, ".qa-vote-count-net > span.qa-netvote-count")
                upvote_count = upvote_element.text.strip()

                view_count = convert_to_int(view_count)
                upvote_count = convert_to_int(upvote_count)
                
                answer_blocks = driver.find_elements(By.CSS_SELECTOR, '.qa-a-list .qa-a-list-item')
                answers = []
                for answer_block in answer_blocks:
                    answer_text_element = answer_block.find_element(By.CSS_SELECTOR, 'form > div > form > div > div')
                    answer_text = answer_text_element.text.strip()

                    answer_date_element = answer_block.find_element(By.CSS_SELECTOR, 'form > div > div.qa-a-footer-details > span > span > span.qa-a-item-when > span > time')
                    answer_date = answer_date_element.text.strip()

                    answer_upvotes_element = answer_block.find_element(By.CSS_SELECTOR, '.qa-vote-count-net > span > span.qa-netvote-count-data')
                    answer_upvotes = answer_upvotes_element.text.strip()

                    answers.append({
                        "text": answer_text,
                        "date": answer_date,
                        "upvotes": int(answer_upvotes)
                    })
                page_data.append({
                        "question_title": question_title,
                        "question_content": question_content,
                        "question_date": question_date,
                        "question_tag": category_text,
                        "question_views": int(view_count),
                        "question_upvotes": int(upvote_count),
                        "answers": answers
                    })
            finally:
                # Возвращаемся на предыдущую страницу
                driver.back()
                # Даем время для возврата страницы к списку вопросов
                time.sleep(2)
        try:
            # Save data to file
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, ensure_ascii=False, indent=4)
            # Taking a nap is always a good idea
            time.sleep(2)
        except Exception as e:
            with open(logsFileName, "a") as logsfile:
                logsfile.write("[Error saving data] " + page_url + " | " + " exception: " + str(e) + "\n")
    except Exception as e:
        with open(logsFileName, "a") as logsfile:
                logsfile.write("[Error loading page] " + page_url + " | " + " exception: " + str(e) + "\n")


if __name__ == '__main__':

    # Explanation : every single q/a page is structured in such a way that
    # by following https://surak.baribar.kz/questions?start=0 , 25, 50, ...
    # you can access each individual page, making it a very nice structure to exploit
    # asynchronous parsing of data
    url_prefix = "https://surak.baribar.kz/questions?start="
    start = 0
    stop = 19976 # the 800th page is questions?start=19975, so stop is 19976 to ensure this last page is also taken into consideration
    step = 25
    

    ThreadPool(5).map(parseAndSaveOnePage, getPageLinks(url_prefix, start, stop, step))