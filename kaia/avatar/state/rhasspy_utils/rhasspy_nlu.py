import numpy
numpy.int = int
numpy.float_ = numpy.float64
from rhasspynlu.intent import Recognition
from rhasspynlu import recognize, parse_ini, intents_to_graph

def escape_for_rhasspy(s):
    disable = set(',.?!')
    return ''.join(c for c in s if c not in disable)


