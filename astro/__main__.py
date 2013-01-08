from .sun import main as sun_main
from .moon import main as moon_main
from .planets import main as planets_main
from .angles import main as angles_main
from .comets import main as comets_main

def main():
    sun_main()
    moon_main()
    planets_main()
    angles_main()
    comets_main()

if __name__ == '__main__':
    main()
