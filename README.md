# html_to_epub
A python script to convert a blog published ebook into a Kindle friendly epub.


#About
I was reading a rather long web series and got tired of keeping track of my place across multiple devices and draining my pathetic phone battery.
Unfortunately the author decided not to provide an ebook in any form in hopes that he would be able to sell a book deal one day. I wish him
luck in that endevour, but I am not content to wait. Python to the rescue.


#Requirements
* python3
* ebooklib - https://github.com/aerkalov/ebooklib
* lxml - https://github.com/lxml/lxml
* tqdm - https://pypi.python.org/pypi/tqdm


#Running 
```bash
python html_to_epub.py --help
python html_to_epub.py --config books/parahumans/config.yaml
```

#Config
Disclaimer: I have only used this on a couple websites so there are probably a million nuances that will break this for other websites


That said, I designed it to be as generic as possible. If you have a (very) well structured website and you are good with css selectors you could turn a website 
into an epub with a simple yaml file like this one:
```yaml
cache: './cache/html/parahumans'
callbacks: 'books.parahumans.parahumans.ParahumansCallbacks'
book:
    title: Parahumans - Worm
    author: Wildbow
    epub_filename: ./books/parahumans/parahumans.epub
    css_filename: 'kindle.css'
    entry_point: 'https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-1-gestation/1-01/'
    chapter:
        title_css_selector: 'h1.entry-title a, h1.entry-title'
        section_css_selector: 'h1.entry-title a, h1.entry-title'
        text_css_selector: 'div.entry-content p'
        next_chapter_css_selector: 'div.entry-content a[title="Next Chapter"], div.entry-content a:not([title])'
```


Some interesting things to note in the config are cache, callbacks and the various css selectors. More on these below. We navigate the web site like a linked list, 
locating links to the next chapter until we cant find them anymore. CSS selectors are used to identify what we care about on a page, with optional callback hooks to 
further parse html elements in python. The css selectors are lxml selectors which are compiled to xpaths under the hood. They implement the vast magority of 
css selector features but there are limitations I ran in to during testing, though I am have having trouble finding a concise explanation of the limitations right now.


##cache
The first time we visit a webpage, it is cached locally. Future runs will use the cache file unless you run with the `--clear-cache` flag. The directory will be created if it does not exist
but there is no expiration or cleanup done by the script unless explicitly ran with the `--clear-cache` flag


##callbacks
The location of a python class which implements the [Callbacks](lib/callbacks.py) base class. This string is used to dynamically import your python module and should be
the module path followed by the class name. The file must be in this python module. See [AnathemaCallbacks](books/anathema/anathema.py) and [ParahumanCallbacks](book/parahumans/parahumans.py)
for examples. Sane defaults have been provided in the [Callbacks](lib/callbacks.py) base class, you only need to override a method if you need futher control of the html parsing. 
Web pages are often a mess and can become a nightmare, if not downright impossible, to parse with pure css selectors.


```python
from lib.callbacks import Callbacks
import re

class ParahumansCallbacks(Callbacks):

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


##entry_point.entry_point
The entry point on the website for building the ebook. This should be the first chapter in the book, with a link to the next chapter which the script
cant walk through to the end of the book. By defaults the order of the chapters will be the same that are encountered while navigating the web page. 
This behavior can be overridden by overriding `Callbacks.sort_chapters(chapters)`


##chapter.title_css_selector
Related callback: `Callbacks.chapter_title_callback(selector_matches)`


CSS selector used on each chapter on the table of contents page to identify the title of the chapter. This is put into the chapter body of the epub as a header and also used when building the navigational
structures required by the epub standard. This needs to uniquely identify an element for the title, by default it will use the text of the first match it finds if there are multiple.


##chapter.section_css_selector
Related callback: `Callbacks.chapter_section_callback(selector_matches)`


Similar to the title css selector. Used when building the ebooks table of contents to group related chapters.

1. Introduction
  1. Chapter 1
  2. Chapter 2
2. Epilogue
  1. Chapter 3
  2. Chapter 3

Introduction and Epilogue would be the sections while chapter 1-4 would be the titles. Like the title, this needs to be uniquely identifiable. 


This can be a huge pain in the ass and isnt always applicable so I plan on making this optional in the future.


##chapter.text_css_selector
Related callback: `Callbacks.chapter_text_callback(selector_match)`


CSS selector used to identify the chapter body on the web page.


##chapter.next_chapter_css_selector
Related callback: `Callbacks.chapter_next_callback(selector_matches)`


CSS selector used to identify the link to the next chapter.


##css_filename
The css file used for styling the epub. I've included a default style sheet that makes books look decent in general, though it is desiged for the Kindle specifically. Feel free to provide your own, just
change this to a relative or absolute path to the file.
