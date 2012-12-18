Some programs I've written using PyEphem.

PyEphem can be found at:
    http://rhodesmill.org/pyephem/

I started out writing this in Python 2.7, but I'm now converting
to Python 3.3

I usually run this in a virtual environment. Once you have
Python 3.3:

    pyvenv ~/venv/astro  # or wherever you'd like it
    # I use virtualenvwrapper to manage the virtual environments,
    # so the workon command puts me in the right spot.
    workon astro
    # Install distribute. I keep a local copy handy
    python ~/Dropbox/src/distribute_setup.py
    # Check the version, usually:  distribute 0.6.30
    easy_install --version
    # Now install ephem. I keep a local copy
    easy_install ~/Dropbox/src/ephem-3.7.5.1.tar.gz
    # I usually work directly in the repository
    cd ~/github/astro
