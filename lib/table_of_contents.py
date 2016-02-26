import lxml.html
from lxml.cssselect import CSSSelector
from collections import OrderedDict
from urllib.request import urlopen
from tqdm import tqdm
import yaml

from .chapter import Chapter

class TableOfContents:
    
    def __init__(self, config):
        self.config = config
        self.tree = None
        self.chapters = None     
 
    def load_html(self):
        response = urlopen(self.config.book.table_of_contents.url)
        self.tree = lxml.html.fromstring(response.read().decode('utf-8', 'ignore'))
        response.close()

        return self.tree

    def get_chapters(self):
        chapters = OrderedDict()
        sel = CSSSelector(self.config.book.table_of_contents.chapter_link_css_selector)

        for link in tqdm(sel(self.tree)):
            href = link.get('href')
            if not href.startswith('https://'):
                href = 'https://' + href

            if href not in chapters:
                chapters[href] = Chapter(href, self.config)
        self.chapters = list(chapters.values())

        return self.chapters
