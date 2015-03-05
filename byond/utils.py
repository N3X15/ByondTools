import hashlib, ast, os, time, sys
import operator as op

def clock():
    if sys.platform == 'win32':
        return time.clock()
    else:
        return time.time()
    
def md5sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        while True:
            buf = f.read(4096)  # 128 is smaller than the typical filesystem block
            if not buf:
                break
            d.update(buf)
        return d.hexdigest().upper()

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor}

def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr).body[0].value)  # Module(body=[Expr(value=...)])

def getElapsed(start):
    return '%d:%02d:%02d.%03d' % reduce(lambda ll, b : divmod(ll[0], b) + ll[1:], [((clock() - start) * 1000,), 1000, 60, 60])

def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll, b : divmod(ll[0], b) + ll[1:], [(t * 1000,), 1000, 60, 60])
        
class TimeExecution(object):
    def __init__(self, label):
        self.start_time = None
        self.label = label
    
    def __enter__(self):
        self.start_time = clock()
        return self
    
    def __exit__(self, type, value, traceback):
        logging.info('  Completed in {1}s - {0}'.format(self.label, secondsToStr(clock() - self.start_time)))
        return False

class ProfilingTarget:
    def __init__(self, name):
        self.name = name
        self.calls = 0
        self.elapsed = 0
        self.start_time = 0
        
    def start(self):
        start_time = clock()
        
    def end(self):
        el = clock() - self.start_time
        calls += 1
        elapsed += el
        return el
    
    def __str__(self):
        return "{} - C: {}, E: {}, A: {}".format(self.name, self.calls, getElapsed(self.elapsed), getElapsed(self.elapsed / self.calls))
    
    def ToCSV(self):
        return "{},{},{},{}".format(self.name, self.calls, getElapsed(self.elapsed), getElapsed(self.elapsed / self.calls))
    
class Profiler:
    def __init__(self):
        self.targets = {}

def eval_(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.operator):  # <operator>
        return operators[type(node)]
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return eval_(node.op)(eval_(node.left), eval_(node.right))
    else:
        raise TypeError(node)
    

_ROOT = os.path.abspath(os.path.dirname(__file__))

def get_data(path):
    return os.path.join(_ROOT, 'data', path)

def get_stdlib(path=''):
    if path != '':
        return os.path.join(get_data('stdlib'), path)
    return get_data('stdlib')


try:
    from line_profiler import LineProfiler

    def do_profile(follow=[]):
        def inner(func):
            def profiled_func(*args, **kwargs):
                try:
                    profiler = LineProfiler()
                    profiler.add_function(func)
                    for f in follow:
                        profiler.add_function(f)
                    profiler.enable_by_count()
                    return func(*args, **kwargs)
                finally:
                    profiler.print_stats()
            return profiled_func
        return inner

except ImportError:
    def do_profile(follow=[]):
        "Helpful if you accidentally leave in production!"
        def inner(func):
            def nothing(*args, **kwargs):
                return func(*args, **kwargs)
            return nothing
        return inner
