from typing import Generator, List, Callable
import requests
from bs4 import BeautifulSoup, Tag, ResultSet
from crawler import VnExpress

class MainCategory:

    def __init__(self, title:str, href:str):
        self.title = title
        self.__href = href

    def get_full_url(self):
        return 'https://vnexpress.net'+self.__href

    def get_label(self):
        name = self.title.replace(" ", "_")
        return "__label__{0}".format(name) 

    def __str__(self):
        return '<MainCategory {0}>'.format(self.title)

    def __repr__(self):
        return '<MainCategory {0}>'.format(self.title)


def get_vnexpress_menus(html:str)-> List[MainCategory]:

    def __has_menu_a_tag(tag: Tag):
        return (tag.name == 'a' 
        and tag.has_attr('title') 
        and tag.has_attr('href') 
        and tag.has_attr('data-medium') 
        and tag.attrs['data-medium'].startswith('Menu')
        and len(tag.attrs) == 3)

    def __a_tag_to_main_category(tag: Tag):
        return MainCategory(tag.attrs['title'], tag.attrs['href'])

    soup = BeautifulSoup(html, 'lxml')
    a_tags:ResultSet = soup.find_all(__has_menu_a_tag)

    return [__a_tag_to_main_category(a_tag) for a_tag in a_tags]


def get_article_urls_at_page(category: MainCategory, page:int)->Generator:
    """
    Dựa theo category truyền vào, lấy ra tất cả các liên kết tới bài viết thuộc thể loại đó tại một trang cụ thể.
    """
    url = category.get_full_url()+'-p{0}'.format(page)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    article_tags = soup.find_all('article', {'class': 'item-news item-news-common'})
    for tag in article_tags:
        try:
            yield tag.h3.a.attrs['href']
        except:
            continue

def get_category_of_a_article(article_url: str) -> MainCategory:
    r = requests.get(article_url)
    soup = BeautifulSoup(r.text, 'lxml')
    ul_header: Tag = soup.find('ul', {'class': 'breadcrumb'})
    a_tag = ul_header.li.a
    return MainCategory(a_tag.attrs['title'],a_tag.attrs['href'])


class VnExpressCrawler:

    def __init__(self, categories:List[MainCategory], pages:int, pre_progress:Callable[[str], str]):
        """
        @pre_progress: Một hàm tiền xử lý nội dung của bài viết.
        """
        self.categories = categories
        self.pages = pages
        self.pre_progress = pre_progress

    def get_datas_train(self)-> Generator:
        for category in self.categories:
            url_generators = [get_article_urls_at_page(category, page) for page in range(1, self.pages+1)]
            for url_generator in url_generators:
                for article_url in url_generator:
                    try:
                        content = VnExpress.get_article_content(article_url)
                        data = category.get_label() + ' ' + self.pre_progress(content)
                        yield data
                    except:
                        continue

    def to_data_training_file(self, file_path:str):
        data_trains = self.get_datas_train()
        for data_train in data_trains:
            with open(file_path, 'a', encoding='utf') as f:
                f.write(data_train)
                f.write('\n')
            


r = requests.get('https://vnexpress.net/')
categories = get_vnexpress_menus(r.text)

vnexpress_crawler = VnExpressCrawler(categories, 1, lambda x: x)
vnexpress_crawler.to_data_training_file('data_train_2.txt')
