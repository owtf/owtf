import os
import shutil
import subprocess


# FIXME: Do not remove user's results. Need OWTF to fix its custom profiles
# options.
DIR_SCRIPTS = 'scripts'
DB_SETUP_SCRIPT = 'db_setup.sh'
DIR_OWTF_REVIEW = 'owtf_review'


def db_setup(cmd):
    """Reset OWTF database."""
    if cmd not in ['clean', 'init']:
        return
    pwd = os.getcwd()
    db_process = subprocess.Popen(
        "/usr/bin/echo '\n' | %s %s" % (
            os.path.join(pwd, DIR_SCRIPTS, DB_SETUP_SCRIPT),
            cmd),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    db_process.wait()


def clean_owtf_review():
    """Remove OWTF owtf_review output directory."""
    pwd = os.getcwd()
    shutil.rmtree(os.path.join(pwd, DIR_OWTF_REVIEW), ignore_errors=True)
