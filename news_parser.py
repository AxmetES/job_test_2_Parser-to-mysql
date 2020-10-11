import os

import pymysql
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from datetime import datetime, timedelta
from urllib.parse import urljoin
from environs import Env

env = Env()
env.read_env()


def get_soup(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def int_value_from_ru_month(date_str):
    RU_MONTH_VALUES = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 10,
        'декабря': 12,
    }
    for k, v in RU_MONTH_VALUES.items():
        date_str = date_str.replace(k, str(v))
    return date_str


def get_image(image_url_fragment):
    url = urljoin('https://tengrinews.kz', image_url_fragment)
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def get_commets(news_url, browser, item_id, conn):
    print(news_url)
    browser.get(news_url)

    element = browser.find_element_by_xpath('//span[contains(text(), "Показать комментарии")]')
    browser.execute_script("arguments[0].click();", element)
    comments = browser.find_elements_by_class_name('tn-comment-item-content')
    for element in comments:
        author = element.find_element_by_class_name('tn-user-name').text
        date = element.find_element_by_tag_name('time').text
        publish_datetime = datetime.strptime(date, '%Y-%m-%d %H:%M')
        comment = element.find_element_by_class_name('tn-comment-item-content-text').text

        parse_datetime = datetime.now()
        write_comment_to_db(item_id, author, publish_datetime, comment, parse_datetime, conn)


def serialize_news(news_url, browser, conn):
    try:
        text_container = []
        page = get_soup(news_url)
        page_title = page.find('h1', class_='tn-content-title')
        try:
            page_title.span.decompose()
        except AttributeError as msg:
            print(msg)
            date_time = page.find('time', class_='tn-visible@t').text
        else:
            date_time = page.find('ul', class_='tn-data-list').find('time').text

        if 'сегодня' in date_time:
            today = date_time.replace('сегодня', str(datetime.now().date()))
            publish_time = datetime.strptime(today, '%Y-%m-%d, %H:%M')
        elif 'вчера' in date_time:
            yesterday = date_time.replace('вчера', str(datetime.now().date() - timedelta(1)))
            publish_time = datetime.strptime(yesterday, '%Y-%m-%d, %H:%M')
        else:
            date_time_str = int_value_from_ru_month(date_time)
            publish_time = datetime.strptime(date_time_str, '%d %m %Y, %H:%M')
        title = page_title.text
        post_tags = page.select('div.tn-news-text p')
        del post_tags[-1]
        for text in post_tags:
            text_container.append(text.text)
        content = ''.join(text_container)
        parse_datetime = datetime.now()
        item_id = write_item_to_db(news_url, title, content, publish_time.date(), publish_time, parse_datetime, conn)

        get_commets(news_url, browser, item_id, conn)

    except AttributeError:
        print('не рядовая статья')


def write_item_to_db(url, title, content, publish_datetime, publish_date, parse_datetime, conn):
    try:
        with conn.cursor() as cursor:
            sql = f"INSERT INTO `items` (`news_link`, `title`, `content`, `publish_date`," \
                  f" `publish_datetime`, `parse_date`) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (url, title, content, publish_date, publish_datetime, parse_datetime))

        conn.commit()

        with conn.cursor() as cursor:
            sql = "SELECT `id` FROM `items` WHERE `title`=%s"
            cursor.execute(sql, (title,))
            result = cursor.fetchone()
    except pymysql.OperationalError as msg:
        print(f"error {msg}")
    return result


def write_comment_to_db(item_id, author, publish_datetime, comment, parse_date, conn):
    try:
        with conn.cursor() as cursor:
            sql = f"INSERT INTO `comments` (`item_id`, `author`, `date`, `comment`, `parse_date`) VALUES (%s, %s, %s, %s,%s)"
            cursor.execute(sql, (item_id['id'], author, publish_datetime, comment, parse_date))

        conn.commit()
    except pymysql.OperationalError as msg:
        print(f"error {msg}")


def get_con():
    con = pymysql.connect(host='localhost', user=os.getenv('DB_USER', 'admin_db'),
                          password=os.getenv('DB_PASSWORD', '123456Aes'), db='news_db', charset='utf8mb4',
                          port=3306, cursorclass=pymysql.cursors.DictCursor)
    return con


if __name__ == '__main__':
    chromedriver = './chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(executable_path=chromedriver, chrome_options=options)

    conn = get_con()
    news_urls = []
    main_url = 'https://tengrinews.kz/'
    news = get_soup(main_url).select('div.tn-tape-item')
    for new in news:
        news_urls.append(new.select_one('a')['href'])
    for url in news_urls:
        if 'http' not in url:
            serialize_news(f'https://tengrinews.kz{url}', browser, conn)
