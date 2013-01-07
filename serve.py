import bottle
route = bottle.route
import astro.sun
import astro.angles

@route('/')
def main():
    obj = astro.angles.get_angle_data()
    return vars(obj)

if __name__ == '__main__':
    bottle.run(reloader=True, port=8000)
