import lxml.html
from lxml.cssselect import CSSSelector
from collections import OrderedDict
from tqdm import tqdm
import yaml, logging

from .chapter import Chapter
from .util import Network

class TableOfContents:
    
    def __init__(self, config, htmlCallbacks):
        self.config = config
        self.htmlCallbacks = htmlCallbacks
        self.url = Network.clean_url(config.book.table_of_contents.url)
        self.cache_filename = Network.cache_filename(self.config.cache, self.url)
        self.tree = None
 
    def load_html(self):
        self.tree = Network.load_and_cache_html(self.url, self.cache_filename)

    def get_chapters(self):
        chapters = OrderedDict()
        match = CSSSelector(self.config.book.table_of_contents.chapter_link_css_selector)

        chapters = OrderedDict()

        for link in tqdm(match(self.tree), disable=self.config.debug):
            link = self.htmlCallbacks.toc_chapters_callback(link)
            
            chapter = Chapter(link.get('href'), self.config, self.htmlCallbacks)

            if chapter is not None and chapter.url not in chapters:
                chapters[link.get('href')] = chapter

        return list(chapters.values())
