import datetime
from doit.tools import timeout

def task_satellites():
    'Periodically retrieve the most recent satellite elements.'
    # TODO this won't work yet.
    return {
        'actions': ['python -m astro.satellites --retrieve'],
        'uptodate': [timeout(datetime.timedelta(days=3))],
        'clean': True,
        'file_dep': ['visual.txt'],
    }
