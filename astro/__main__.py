import curses
import ephem
import threading
from .mainloop import MainLoop
from .skyposition import SkyPosition
#from .location import Location

def main():
    pass

def window_main(w):
    curses.start_color()
    curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    w.timeout(1000)

    loop_thread = MainLoop(w)
    loop_thread.start()
    loop_thread.join()


if __name__ == '__main__':
    #curses.wrapper(main)
    main()
