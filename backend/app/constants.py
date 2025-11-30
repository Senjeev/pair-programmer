PYTHON_KEYWORDS = [
    "def", "class", "if", "elif", "else", "for", "while", "try", "except", "finally",
    "import", "from", "as", "return", "yield", "with", "lambda", "break", "continue",
    "pass", "global", "nonlocal", "assert", "raise"
]

PYTHON_BUILTINS = [
    "abs","all","any","ascii","bin","bool","bytearray","bytes","callable","chr","classmethod",
    "compile","complex","delattr","dict","dir","divmod","enumerate","eval","exec","filter",
    "float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input",
    "int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview","min",
    "next","object","oct","open","ord","pow","print","property","range","repr","reversed","round",
    "set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip"
]

PYTHON_METHODS = [
    "append","extend","insert","remove","pop","clear","sort","reverse","copy","keys","values",
    "items","get","update","setdefault","split","join","replace","strip","lower","upper",
    "startswith","endswith","find","index","count","format","read","write","close","seek",
    "encode","decode"
]

PYTHON_MODULES = [
    "os","sys","math","random","json","re","datetime","time","collections","itertools",
    "functools","subprocess","threading","asyncio","pathlib","shutil","socket","logging",
    "http","email","argparse","pickle","copy","heapq","uuid","glob","tempfile","traceback"
]

ALL_WORDS = (PYTHON_KEYWORDS + PYTHON_BUILTINS + PYTHON_METHODS + PYTHON_MODULES)