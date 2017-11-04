import os


DIR_OWTF_REVIEW = 'owtf_review'
DIR_OWTF_LOGS = 'logs'


def load_log(name, dir_owtf_review=DIR_OWTF_REVIEW, dir_owtf_logs=DIR_OWTF_LOGS, absolute_path=False):
    """Read the file 'name' and returns its content."""
    if not name.endswith('.log'):
        name += '.log'
    if not absolute_path:
        fullpath = os.path.join(os.getcwd(), dir_owtf_review, dir_owtf_logs, name)
    else:
        fullpath = name
    with open(fullpath, 'r') as f:
        return f.readlines()
