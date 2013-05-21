import platform


def static_bootstrap(request):
    """ Our local server handles this file, so this is
        an easy way to deal with it.
    """
    return {
        'static_bootstrap': "http://{}/bootstrap/css/bootstrap.css".format(
            platform.node()),
    }
