import string
import sys
from secrets import choice


def check_result(result):
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()


def generate_password(length):
    return "".join(choice(string.ascii_letters + string.digits) for i in range(length))
