from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import requests


def get_soup(main_url):
    response = requests.get(main_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def get_image(image_url_fragment):
    url = urljoin('https://tengrinews.kz', image_url_fragment)
    response = requests.get(url)
    response.raise_for_status()
    return response.content


if __name__ == '__main__':
    text_container = []
    url = 'https://tengrinews.kz/kazakhstan_news/alimentschik-lishilsya-kvartiryi-v-kokshetau-416538/'
    page = get_soup(url)
    page_title = page.find('h1', class_='tn-content-title')
    try:
        page_title.span.decompose()
    except AttributeError as msg:
        print(msg)
        date = page.find('time', class_='tn-visible@t').text
    else:
        date = page.find('ul', class_='tn-data-list').find('time').text
    title = page_title.text

    image_url_fragment = page.select('div.tn-news-content img')[0]['src']
    post_tags = page.select('div.tn-news-text p')
    del post_tags[-1]
    for text in post_tags:
        text_container.append(text.text)
    content = ''.join(text_container)
    image_file = get_image(image_url_fragment)
    with open(f'./image.jpg', 'wb') as file:
        file.write(image_file)

    print(content)
    print(title)
    print(date)

    chromedriver = './chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(executable_path=chromedriver, chrome_options=options)
    browser.get(url)

    element = browser.find_element_by_xpath('//span[contains(text(), "Показать комментарии")]')
    browser.execute_script("arguments[0].click();", element)
    commets = browser.find_elements_by_class_name('tn-comment-item-content')
    for commet in commets:
        author = commet.find_element_by_class_name('tn-user-name')
        print(author.text)
        time = commet.find_element_by_tag_name('time')
        print(time.text)
        text = commet.find_element_by_class_name('tn-comment-item-content-text')
        print(text.text)
