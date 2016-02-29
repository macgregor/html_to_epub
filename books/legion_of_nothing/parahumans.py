from lib.callbacks import Callbacks
import re

class ParahumansCallbacks(Callbacks):

    def __init__(self, config):
        self.config = config

    def chapter_text_callback(self, selector_match):
        if len(selector_match.cssselect('a')) == 0:
            return selector_match
        else:
            return None

    def chapter_title_callback(self, selector_matches):
        title = None
        for match in selector_matches:
            if match.text is not None:
                title = match.text
                break
        return title

    def chapter_section_callback(self, selector_matches):
        section_regex = '^(\w+)\s*.*$'
        title = self.chapter_title_callback(selector_matches)
        return re.match(section_regex, title).group(1)
