import lxml.html
from lxml.cssselect import CSSSelector
from collections import OrderedDict
from tqdm import tqdm
import logging

from .chapter import Chapter, ChapterMock
from .util import Network

'''
TableOfContents class - parses the table of contents web page (config.book.table_of_contents.url) and
                        constructs a list of chapters based on links it finds
'''
class TableOfContents:
    
    def __init__(self, config, callbacks):
        self.config = config
        self.callbacks = callbacks
        self.url = Network.clean_url(config.book.table_of_contents.url)
        self.cache_filename = Network.cache_filename(self.config.cache, self.url)
        self.tree = None
 
    '''
    Cache (if necessary) and load html dom into memory
    '''
    def load_html(self):
        self.tree = Network.load_and_cache_html(self.url, self.cache_filename)

    '''
    Parse dom for uniqueue links matching the config.book.table_of_contents.chapter_link_css_selector and 
    the user's callback. Maintains order of the links found by default. This can be changed later
    by overriding Callbacks.sort_chapters()
    '''
    def get_chapters(self):
        chapters = OrderedDict()
        match = CSSSelector(self.config.book.table_of_contents.chapter_link_css_selector)

        chapters = OrderedDict()

        for link in tqdm(match(self.tree), disable=self.config.debug):
            # link will be None if the user wants to ignore it
            link = self.callbacks.toc_chapters_callback(link)

            if link is not None and link.get('href') is not None:
                # if toc_break flagg set, create ChapterMocks so we dont actually download the chapters
                if not self.config.toc_break:
                    chapter = Chapter(link.get('href'), self.config, self.callbacks)
                else:
                    chapter = ChapterMock(link.get('href'), self.config, self.callbacks)

                # make sure this url/chapter isnt already in the list
                if chapter is not None and chapter.url not in chapters:
                    chapters[link.get('href')] = chapter

        return list(chapters.values())
