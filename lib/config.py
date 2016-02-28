import yaml, logging

class TableOfContentsConfig:
    def __init__(self, yml):
        self.url = yml['url']
        self.chapter_link_css_selector = yml['chapter_link_css_selector']

    def __str__(self):
        return "    Table_of_Contents{{\n      url: '{}'\n      chapter_link_css_selector: '{}'\n    }}".format(self.url, self.chapter_link_css_selector)

class ChapterConfig:
    def __init__(self, yml):
        self.title_css_selector = yml['title_css_selector']
        self.text_css_selector = yml['text_css_selector']
        self.section_css_selector = yml['section_css_selector']

    def __str__(self):
        return "    Chapter{{\n      title_css_selector: '{}'\n      text_css_selector: '{}'\n      section_css_selector: '{}'\n    }}".format(self.title_css_selector, self.text_css_selector, self.section_css_selector)

class BookConfig:
    def __init__(self, yml):
        self.title = yml['title']
        self.author = yml['author']
        self.epub_filename = yml['epub_filename']
        self.table_of_contents = TableOfContentsConfig(yml['table_of_contents'])
        self.chapter = ChapterConfig(yml['chapter'])
        self.css_filename = yml['css_filename']

    def __str__(self):
        return "  Book{{\n    title: '{}'\n    author: '{}'\n    epub_filename: '{}'\n    css_filename: '{}'\n{}\n{}\n  }}".format(self.title, self.author, self.epub_filename, self.css_filename, str(self.table_of_contents), str(self.chapter))

class Config:

    def __init__(self, filename, debug=False, toc_break=False):
        logging.getLogger().debug('Loading yaml config ' + filename)
        with open(filename, 'r') as ymlfile:
            config = yaml.load(ymlfile)

        self.book = BookConfig(config['book'])
        self.cache = config['cache']

        if 'html_callbacks' in config:
            self.html_callbacks = config['html_callbacks']
        else:
            self.html_callbacks = None

        self.debug = debug
        self.toc_break = toc_break

    def __str__(self):
        return "\nConfig{{\n  cache: '{}'\n  html_callbacks: {}\n{}\n}}".format(self.cache, self.html_callbacks, str(self.book))
