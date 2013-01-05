import os

def _astro():
    ASTRO_FOLDER = os.path.expanduser('~/.astro')
    if not os.path.exists(ASTRO_FOLDER):
        os.makedirs(ASTRO_FOLDER)
    return ASTRO_FOLDER


def astro_path(name):
    return os.path.join(_astro(), name)
