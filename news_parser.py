from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from urllib.parse import urljoin
import pprint


def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    return soup


def get_image(image_url_fragment):
    url = urljoin('https://tengrinews.kz', image_url_fragment)
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def get_commets(news_url, browser):
    news_comments = []
    print(news_url)
    browser.get(news_url)

    element = browser.find_element_by_xpath('//span[contains(text(), "Показать комментарии")]')
    browser.execute_script("arguments[0].click();", element)
    commets = browser.find_elements_by_class_name('tn-comment-item-content')
    for text in commets:
        author = text.find_element_by_class_name('tn-user-name').text
        date = text.find_element_by_tag_name('time').text
        comment = text.find_element_by_class_name('tn-comment-item-content-text').text
        news_comments.append({'author': author,
                              'date': date,
                              'comment': comment,
                              })
    return news_comments


def serialize_news(news_url, browser):
    try:
        text_container = []
        page = get_soup(news_url)
        page_title = page.find('h1', class_='tn-content-title')
        print(news_url)
        try:
            page_title.span.decompose()
        except AttributeError as msg:
            print(msg)
            date = page.find('time', class_='tn-visible@t').text
        else:
            date = page.find('ul', class_='tn-data-list').find('time').text

        title = page_title.text
        # image_url_fragment = page.select('div.tn-news-content img')[0]['src']
        post_tags = page.select('div.tn-news-text p')
        del post_tags[-1]
        for text in post_tags:
            text_container.append(text.text)
        content = ''.join(text_container)
        # image_file = get_image(image_url_fragment)
        # with open(f'./image.jpg', 'wb') as file:
        #     file.write(image_file)

        comments = get_commets(news_url, browser)

        return {'news_link': news_url,
                'title': title,
                'content': content,
                'published': date,
                'comments': comments, }
    except AttributeError:
        print('не рядовая статья')


if __name__ == '__main__':
    chromedriver = './chromedriver'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome(executable_path=chromedriver, chrome_options=options)

    news_urls = []
    news_catalog = []
    main_url = 'https://tengrinews.kz/'
    news = get_soup(main_url).select('div.tn-tape-item')
    for new in news:
        news_urls.append(new.select_one('a')['href'])
    for url in news_urls:
        if 'http' not in url:
            news_catalog.append(serialize_news(f'https://tengrinews.kz{url}', browser))
        else:
            pass

    with open('./news_catalog.txt', 'w') as file:
        file.write(str(news_catalog))
