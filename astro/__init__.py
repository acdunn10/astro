# -*- coding: utf8
import os

def astro_config(name):
    "A folder to store stuff we download"
    path = os.path.expanduser('~/.astro')
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, name)

