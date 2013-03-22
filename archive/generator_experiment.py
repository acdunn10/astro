""" Experiment with generators. See PEP 342"""
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
        body, date, observer = token
        observer.date = date
        body.compute(observer)
        destination.send(body)

@consumer
def compute(destination):
    while True:
        body, date = (yield)
        body.compute(date)
        destination.send(body)

@consumer
def display_elongation():
    while True:
        body = (yield)
        print(body.name, body.elong)

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



if __name__ == '__main__':
    date = ephem.now()
    observer = ephem.city('Columbus')
#     pipeline = compute(display_elongation())
#     for planet in PLANETS:
#         pipeline.send((planet(), date))

    pipeline = compute_observer(display_sky_position())
    for planet in PLANETS:
        pipeline.send((planet(), date, observer))
    pipeline.send(None)


