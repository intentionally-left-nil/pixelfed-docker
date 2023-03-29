import string
import sys
import subprocess
from secrets import choice


def check_result(result):
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()


def generate_password(length):
    return "".join(choice(string.ascii_letters + string.digits) for i in range(length))


_docker_compose_prefix = None


def docker_compose_prefix():
    global _docker_compose_prefix
    if _docker_compose_prefix is None:
        auth_prefix = []
        result = subprocess.run(["docker", "info"], capture_output=True)
        if result.returncode != 0:
            result = subprocess.run(["sudo", "docker", "info"], capture_output=True)
            check_result(result)
            auth_prefix = ["sudo"]

        result = subprocess.run(
            auth_prefix + ["docker", "compose", "version"], capture_output=True
        )

        if result.returncode == 0:
            _docker_compose_prefix = auth_prefix + ["docker", "compose"]
        else:
            result = subprocess.run(
                auth_prefix + ["docker-compose", "version"], capture_output=True
            )
            check_result(result)
            _docker_compose_prefix = auth_prefix + ["docker-compose"]
    return _docker_compose_prefix
