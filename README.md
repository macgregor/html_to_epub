# parahumans_scraper
A python script to convert a blog published web series into a Kindle friendly epub.


#About
I was reading a rather long web series and got tired of keeping track of my place across multiple devices and draining my pathetic phone battery.
Unfortunately the author decided not to provide an ebook in any form in hopes that he would be able to sell a book deal one day. I wish him
luck in that endevour, but I am not content to wait. Python to the rescue.


#Requirements
* python3
* ebooklib - https://github.com/aerkalov/ebooklib
* lxml - https://github.com/lxml/lxml
* tqdm - https://pypi.python.org/pypi/tqdm


#Config
Disclaimer: I have only used this on a single website (https://parahumans.wordpress.com/) so there are probably a million nuances that will break this for other websites


That said, I designed it to be as generic as possible. If you have a (very) well structured website and you are good with css selectors you could turn a website 
into an epub with a simple yaml file like this one:
```yaml
cache: './cache/html'
book:
    title: Parahumans - Worm
    author: Wildbow
    epub_filename: ./books/parahumans/parahumans.epub
    css_filename: 'kindle.css'
    table_of_contents:
        url: 'https://parahumans.wordpress.com/table-of-contents/'
        chapter_link_css_selector: 'div.entry-content a:not([href*="share"])'
    chapter:
        title_css_selector: 'h1.entry-title a, h1.entry-title'
        section_css_selector: 'h1.entry-title a, h1.entry-title'
        text_css_selector: 'div.entry-content p'
```


The interesting parts are the table_or_contents url and the various css selectors. The table_of_contents url is the entry point. We go here and get an ordered list
of urls for each chapter of the ebook. CSS selectors are used to identify what we care about on a page.


##cache
The first time we visit a webpage, it is cached locally. Future runs will use the cache file unless you run with the --clear-cache flag


##table_of_contents.url
The entry point on the website for building the ebook. This page should have an ordered list of chapter urls we can use to navigate the rest of the site.


##table_of_contents.chapter_link_css_selector
CSS Selector used on the table of contents page to identify links to turn into chapters.


##chapter.title_css_selector
CSS selector used on each chapter on the table of contents page to identify the title of the chapter. This is put into the chapter body of the epub as a header and also used when building the navigational
structures required by the epub standard. This needs to uniquely identify an element for the title, by default it will use the text of the first match it finds if there are multiple.


##chapter.section_css_selector
Similar to the title css selector. Used when building the ebooks table of contents to group related chapters.
1. Introduction
  1. Chapter 1
  2. Chapter 2
2. Epilogue
  1. Chapter 3
  2. Chapter 3
Introduction and Epilogue would be the sections while chapter 1-4 would be the titles. Like the title, this needs to be uniquely identifiable.


##chapter.text_css_selector
CSS selector used to identify the chapter body on the web page. 


##CSS Selector Limitations
Soemtimes the css selecot doesnt quite get the job done. In these situations you can extend the [HtmlCallbacks](lib/callbacks.py) class to have the program execute custom logic after running the css selector.
the HtmlCallback base class has documentation on the expectations for how to use these functions you can see an example below
```python
from lib.callbacks import HtmlCallbacks
import re

class ParahumansHtmlCallbacks(HtmlCallbacks):

    def __init__(self, config):
        self.config = config

    # called for each element matched by the chapter.text_css_selector
    # this excludes a section at the top and bottom of the chapter body 
    # that contain links to the next and previous chapters
    def chapter_text_callback(self, selector_match):
        if len(selector_match.cssselect('a')) == 0:
            return selector_match
        else:
            return None

    # called when getting a chapter's title, should be a unique match 
    # sometimes the web page put the title in a <h1> tag, other times
    # in a <a> tag inside the <h1> tag
    def chapter_title_callback(self, selector_matches):
        title = None
        for match in selector_matches:
            if match.text is not None:
                title = match.text
                break
        return title

    # called when getting a chapter's section for the table of contents
    # should be a unique match. This web page breaks the story into
    # multiple arcs with many chapters in each arc (e.g. Extermination 8.3)
    # Use a regex to parse out the section
    def chapter_section_callback(self, selector_matches):
        section_regex = '^(\w+)\s*.*$'
        title = self.chapter_title_callback(selector_matches)
        return re.match(section_regex, title).group(1)
```
We then include this in [html_to_epub.py](html_to_epub.py)
```python
from books.parahumans.parahumans import ParahumansHtmlCallbacks

if __name__ == '__main__':
    ...
    book = Book(config, ParahumansHtmlCallbacks(config))
    book.load_html()

    try:
        epub.write_epub(config.book.epub_filename, book.generate_epub(), {})
    except Exception as e:
        print(traceback.format_exc())
```


#Future Improvements
As I find more web sites I want to ebookify Im sure I'll find holes to fill. Id love to not have to write any custom python. lxml uses xpaths under the hood which I might be able to get more precise with
but no one likes writing xpaths either. I'm fine with this for now. Time to go read my book.
