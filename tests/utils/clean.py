import os
import shutil
import subprocess


# FIXME: Do not remove user's results. Need OWTF to fix its custom profiles
# options.
Makefile = 'Makefile'
DIR_OWTF_REVIEW = 'owtf_review'


def db_clean():
    """Reset OWTF database."""
    pwd = os.getcwd()
    db_process = subprocess.Popen(
        "make clean",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    db_process.wait()


def clean_owtf_review():
    """Remove OWTF owtf_review output directory."""
    pwd = os.getcwd()
    shutil.rmtree(os.path.join(pwd, DIR_OWTF_REVIEW), ignore_errors=True)
