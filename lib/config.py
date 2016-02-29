import yaml, logging

class ChapterConfig:
    def __init__(self, yml):
        self.title_css_selector = yml['title_css_selector']
        self.text_css_selector = yml['text_css_selector']
        self.section_css_selector = yml['section_css_selector']
        self.next_chapter_css_selector = yml['next_chapter_css_selector']

    def __str__(self):
        return "    Chapter{{\n      title_css_selector: '{}'\n      text_css_selector: '{}'\n      section_css_selector: '{}'\n      next_chapter_css_selector: '{}'\n    }}".format(self.title_css_selector, self.text_css_selector, self.section_css_selector, self.next_chapter_css_selector)

class BookConfig:
    def __init__(self, yml):
        self.title = yml['title']
        self.author = yml['author']
        self.epub_filename = yml['epub_filename']
        self.chapter = ChapterConfig(yml['chapter'])
        self.css_filename = yml['css_filename']                
        self.entry_point = yml['entry_point']

    def __str__(self):
        return "  Book{{\n    title: '{}'\n    author: '{}'\n    epub_filename: '{}'\n    css_filename: '{}'\n    entry_point: '{}'\n{}\n  }}".format(self.title, self.author, self.epub_filename, self.css_filename, self.entry_point, str(self.chapter))

class Config:

    def __init__(self, filename, debug=False, toc_break=False):
        logging.getLogger().debug('Loading yaml config ' + filename)
        with open(filename, 'r') as ymlfile:
            config = yaml.load(ymlfile)

        self.book = BookConfig(config['book'])
        self.cache = config['cache']

        if 'callbacks' in config:
            self.callbacks = config['callbacks']
        else:
            self.callbacks = None

        if 'max_chapter_iterations' in config:
            self.max_chapter_iterations = config['max_chapter_iterations']
        else:
            self.max_chapter_iterations = 7000

        self.debug = debug
        self.toc_break = toc_break

    def __str__(self):
        return "\nConfig{{\n  cache: '{}'\n  html_callbacks: {}\n{}\n}}".format(self.cache, self.callbacks, str(self.book))
