from abc import ABCMeta, abstractmethod
from lxml.etree import tostring
import logging

'''
Base class used to implement custom callbacks when parsing html. If you cannot identify exactly what you want in a css selector
you can override any and all of these methods to apply custom python logic when scraping html. I tried to apply sensible defaults
in this class so that if you can get by with css selectors you should be able to convert an entire website to epub with just
the yaml configuration file.

Some methods are called on each element that matches a selector, others are called once with all elements that match
a selector. Read the description of each method carefully for what inputs and outputs to expect.
'''
class Callbacks(object, metaclass=ABCMeta):

    def __init__(self, config):
        logging.getLogger().debug('Instantiating Callbacks class')
        self.config = config

    '''
    Callback funtion executed on the result of the css selector in Chapter.get_epub_section(). The section
    must be a unique element. If you cannot identify it purely with a CSS selector, override this method
    to implement custom logic to identify the section

    parameters:
        selector_matches - array of lxml.html elements that match config.book.chapter.section_css_selector

    returns:
        string - The section this chapter should be grouped under in the table of contents in string format
    '''
    def chapter_section_callback(self, selector_matches):
        return selector_matches[0].text

    '''
    Callback function executed on the result of the css selector in Chapter.get_title(). The title
    must be a unique element. If you cannot identify it purely with a CSS selector, override this method
    to implement custom logic to identify the title

    parameters:
        selector_matches - array of lxml.html elements that match config.book.chapter.title_css_selector

    returns:
        string - The title of the chapter in string format
    '''
    def chapter_title_callback(self, selector_matches):
        return selector_matches[0].text


    '''
    Callback function executed for each element matched by the css selector in Chapter.get_text(). Helpful
    for weeding out extra content you dont want in your ebook but cant fit into a selector. If you dont want
    to include a match, simply return None of that element and it will be discarded.

    parameters:
        selector_match - lxml.html element that matches config.book.chapter.text_css_selector

    returns:
        lxml element - The lxml element if you want it included, or None to ignore it
    '''
    def chapter_text_callback(self, selector_match):
        return selector_match

    '''
    Callback function executed on the result of the css selector in Chapter.get_next_chapter(). The next chapter
    must be a unique element. If you cannot identify it purely with a CSS selector, override this method to implement
    custom logic to identify the next chapter link

    parameters:
        selector_matches - array of lxml.html elements that match config.book.chapter.next_chapter_css_selector

    returns:
        string - The url of the next chapter in string format
    '''
    def chapter_next_callback(self, selector_matches):
        for match in selector_matches:
            if 'next' in tostring(match, encoding='unicode').lower():
                return match.get('href')

        return None

    '''
    Callback function executed after html parsing is complete, before generating the epub. Override to implement
    a custom sorting of the chapters based on whatever criteria you want rather than the default order found on
    the table of contents web page.

    parameters:
        chapters - list of chapter objects

    returns:
        list of chapter objects
    '''
    def sort_chapters(self, chapters):
        return chapters
