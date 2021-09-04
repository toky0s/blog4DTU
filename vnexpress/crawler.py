from typing import Any, Dict, List
from bs4.element import ResultSet, Tag
import requests
from bs4 import BeautifulSoup
import json
import urllib3
urllib3.disable_warnings()


class SubCategory:
    def __init__(self, title: str, href: str):
        self.title = title
        self.href = href


class Category:
    def __init__(self, name: str, title: str, data_id: str, root: str, href: str):
        self.name = name
        self.title = title
        self.data_id = data_id
        self.root = root
        self.href = href

    def __str__(self):
        return 'Category {name}'.format(name=self.name)

    def __repr__(self) -> str:
        return '<Category {name}>'.format(name=self.name)


class ArticleInfo:
    def __init__(self, title: str, lead: str, share_url: str, category: Category):
        self.title = title
        self.lead = lead
        self.share_url = share_url
        self.category = category
    
    def __str__(self):
        return 'Article {0}'.format(self.title)

    def __repr__(self):
        return '<Article {0}>'.format(self.title)


class Article:

    def __init__(self, article_info: ArticleInfo, content:str):
        self.article_info = article_info
        self.content = content


class VnExpress:

    HOME_API_JSON_URL = 'https://vnexpress.net/microservice/home'
    HOME_URL = 'https://vnexpress.net/'

    def __init__(self):
        self.html = self.__get_raw_html_page(self.HOME_URL)
        self.soup = self.__get_soup(self.html)
        self.categories = self.__get_categories(self.soup)

    def __get_categories(self, soup: BeautifulSoup) -> List[Category]:

        def has_data_id_attribute(tag: Tag):
            return tag.has_attr('data-id') and tag.name == 'li'

        def li_tag_to_category(li_tag: Tag) -> Category:
            name: str = li_tag['class'][0]
            title: str = li_tag.a['title']
            data_id: str = li_tag['data-id']
            root: str = self.HOME_URL
            href: str = li_tag.a['href']
            return Category(name, title, data_id, root, href)

        main_nav: Tag = soup.find(
            'section', {'class': 'section wrap-main-nav'})
        li_tags: ResultSet = main_nav.find_all(has_data_id_attribute)
        categories: List[Category] = [li_tag_to_category(tag) for tag in li_tags]
        return categories

    def __get_raw_html_page(self, url: str) -> str:
        re = requests.get(url)
        return re.text

    def __get_soup(self, html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, 'lxml')
        return soup

    def __get_articles_as_json(self, category: Category, limit: int = 50) -> Any:
        url = 'https://gw.vnexpress.net/mv?site_id=1000000&category_id={0}&type=1&limit={1}&data_select=article_id,article_type,title,share_url,thumbnail_url,publish_time,lead,privacy,original_cate,article_category&thumb_size=300x180&thumb_quality=100&thumb_dpr=1,2&thumb_fit=crop'.format(category.data_id, limit)
        r = requests.get(url, 
                        headers={'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55'},
                        verify=False)
        json_text = json.loads(r.text)
        return json_text
    
    def get_article_infoes(self,category: Category)->List[ArticleInfo]:

        def json_to_artice(article_json:Any, category:Category)->ArticleInfo:
            title = article_json['title']
            lead = article_json['lead']
            share_url = article_json['share_url']
            category:Category = category
            return ArticleInfo(title=title, lead=lead, share_url=share_url,category=category)

        json_data = self.__get_articles_as_json(category)
        data_list = json_data['data'][category.data_id]['data']
        return [ json_to_artice(o, category) for o in data_list]
        
    @staticmethod
    def get_article_content(article_url:str):
        """
        Lấy ra nội dung của 1 bài viết dựa theo url truyền vào.
        """
        r = requests.get(article_url)
        print(r.url)
        soup = BeautifulSoup(r.text, 'lxml')
        p_tags:List[Tag] = soup.find_all('p', {'class':'Normal'})
        return ' '.join([p.text for p in p_tags])


def article_infor_to_article(article_info: ArticleInfo):
    content = VnExpress.get_article_content(article_info.share_url)
    return Article(article_info, content)


def article_to_json(article: Article)->Any:
    return {
        "category": article.article_info.category.data_id,
        "title": article.article_info.title,
        "lead": article.article_info.lead,
        "share_url": article.article_info.share_url,
        "content": article.content
    }


def category_to_label(category_name:str):
        name = category_name.replace(" ", "_")
        return "__label__{0}".format(name) 

def category_article_json():
    vnexpress = VnExpress()
    categories:List[Category] =vnexpress.categories
    json_results = []
    for category in categories:
        try:
            article_infoes = vnexpress.get_article_infoes(category)
            articles = [ article_infor_to_article(article_info) for article_info in article_infoes ]
            articles_json = [article_to_json(article) for article in articles]

            json_object = {
                "category":category.name,
                "articles":articles_json
            }
            
            json_results.append(json_object)
        except Exception as e:
            continue
    return json_results

def text_preprocess(document: str) -> str:
    # your handler here
    return document

def category_article_text_file(file_path:str):
    vnexpress = VnExpress()
    categories:List[Category] =vnexpress.categories
    for category in categories:
            try:
                article_infoes = vnexpress.get_article_infoes(category)
            except:
                continue
            _50_first_articles = []
            for article in article_infoes:
                a:Article = article_infor_to_article(article)
                if a.content.replace('\n', ' ') == "":
                    continue
                content = category_to_label(category.title)+" "+text_preprocess(a.content.replace('\n', ' '))
                _50_first_articles.append(content)

            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(_50_first_articles))
            break


if __name__ == "__main__":
    # json_object = category_article_json()
    # with open('data_train', 'w', encoding='utf-8') as f:
    #     json.dump(json_object, f, ensure_ascii=False)

    category_article_text_file('data_train.txt')
