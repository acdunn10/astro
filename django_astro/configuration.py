import os
import configparser
import ephem

class AstroConfig(configparser.ConfigParser):
    CONFIG_PATH = os.path.expanduser('~/.astro/config.ini')

    def __init__(self):
        super().__init__(
            defaults={'observer': 'Columbus'},
            allow_no_value=True)
        self.read(self.CONFIG_PATH)

    def as_list(self, option, section=None):
        if section is None:
            section = 'DEFAULT'
        items = self[section][option].split('\n')
        items = [i for i in items if i]
        return [i.split('#')[0].strip() for i in items]

    @property
    def observer(self):  # shortcut for common usage
        return ephem.city(self['DEFAULT']['observer'])

    @observer.setter
    def observer(self, value):
        self['DEFAULT']['observer'] = value
        with open(self.CONFIG_PATH, 'w') as f:
            self.write(f)


config = AstroConfig()
