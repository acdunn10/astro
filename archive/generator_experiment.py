""" Experiment with generators. See PEP 342"""
import collections
import ephem

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)

def consumer(func):
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

@consumer
def compute_observer(destination):
    while True:
        token = (yield)
        if token is None:
            destination.send(None)
            break
        body, observer = token
        body.compute(observer)
        destination.send(body)

@consumer
def display_sky_position():
    body_list = []
    while True:
        body = (yield)
        if body:
            body_list.append(body)
        else:
            break
    for body in sorted(body_list, key=lambda x:x.alt, reverse=True):
        print(body.name, body.alt, body.az)

def compute_with_observer(observer, *args):
    for name in args:
        if isinstance(name, collections.Iterable):
            yield from compute_with_observer(observer, *name)
        else:
            body = body_from_name(name)
            body.compute(observer)
            yield body

def body_from_name(name):
    if isinstance(name, type):
        return name()


if __name__ == '__main__':
    date = ephem.now()
    observer = ephem.city('Columbus')
    observer.date = date

#     pipeline = compute_observer(display_sky_position())
#     for planet in PLANETS:
#         pipeline.send((planet(), observer))
#     pipeline.send(None)

    for body in compute_with_observer(observer, ephem.Sun, ephem.Moon, PLANETS):
        print(body.name, body.alt, body.az)


