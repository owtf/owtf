"""
tests.utils
~~~~~~~~~~~

Miscellaneous functions for test cases
"""
import os
import shutil
import subprocess

DIR_OWTF_REVIEW = "owtf_review"
DIR_OWTF_LOGS = "logs"


def db_setup(cmd):
    """Reset OWTF database."""
    if cmd not in ["clean", "init"]:
        return
    formatted_cmd = "make db-{}".format(cmd)
    pwd = os.getcwd()
    db_process = subprocess.Popen(
        "/usr/bin/echo '\n' | %s %s" % (os.path.join(pwd), formatted_cmd),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    db_process.wait()


def clean_owtf_review():
    """Remove OWTF owtf_review output directory."""
    pwd = os.getcwd()
    shutil.rmtree(os.path.join(pwd, DIR_OWTF_REVIEW), ignore_errors=True)


def load_log(
    name,
    dir_owtf_review=DIR_OWTF_REVIEW,
    dir_owtf_logs=DIR_OWTF_LOGS,
    absolute_path=False,
):
    """Read the file 'name' and returns its content."""
    if not name.endswith(".log"):
        name += ".log"
    if not absolute_path:
        fullpath = os.path.join(os.getcwd(), dir_owtf_review, dir_owtf_logs, name)
    else:
        fullpath = name
    with open(fullpath, "r") as f:
        return f.readlines()
