import curses
import threading
import ephem
from .skyposition import SkyPosition

class MainLoop(threading.Thread):
    def __init__(self, w):
        super().__init__()
        self.w = w
        self.keep_alive = True
        self.displays = {}


    def run(self):
        while self.keep_alive:
            date = ephem.now()
            self.w.addstr(0, 0, "{:%H:%M:%S} UT {:11,.5f}".format(
                date.datetime(), date))
            self.w.addstr(0, 40, "{:%H:%M:%S} Local".format(
                ephem.localtime(date)))
            self.w.clrtobot()
            curses.curs_set(0)
            ch = self.w.getch()
            if ch == ord('q'):
                self.keep_alive = False
