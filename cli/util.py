import sys


def check_result(result):
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
