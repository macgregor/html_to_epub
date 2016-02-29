from lib.callbacks import Callbacks
import re

class ParahumansCallbacks(Callbacks):

    def __init__(self, config):
        self.config = config
        self.sections = dict()

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
        section_regex = '^(\w+)\s*(\d*)\\.*(\d*).*$'
        title = self.chapter_title_callback(selector_matches)
        regex_match = re.match(section_regex, title)

        if 'interlude' in regex_match.group(1).lower():
            return self.sections[regex_match.group(2)]

        if regex_match.group(2) not in self.sections:
            self.sections[regex_match.group(2)] = regex_match.group(1)
            

        return self.sections[regex_match.group(2)]
