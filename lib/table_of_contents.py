import lxml.html
from lxml.cssselect import CSSSelector
from collections import OrderedDict
from urllib.request import urlopen
from tqdm import tqdm
import yaml

from .chapter import Chapter

class TableOfContents:
    
    def __init__(self, url):
        self.url = url
        self.tree = None
        self.chapters = None

    def __getstate__(self):
        odict = self.__dict__.copy()
        odict['tree'] = None
        return odict       
 
    def load_dom(self):
        response = urlopen(self.url)
        self.tree = lxml.html.fromstring(response.read().decode('utf-8', 'ignore'))
        response.close()

        return self.tree

    def get_chapters(self, html_cache_location):
        if self.tree is not None:
            chapters = OrderedDict()
            sel = CSSSelector('div.entry-content a:not([href*="share"])')

            for link in sel(self.tree):
                href = link.get('href')
                if not href.startswith('https://'):
                    href = 'https://' + href

                if href not in chapters:
                    chapters[href] = Chapter(href, html_cache_location)
            self.chapters = list(chapters.values())

        return self.chapters
