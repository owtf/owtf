"""
owtf.runner.commands.init
~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import, print_function

import os
import click


@click.command()
@click.pass_context
def init(ctx):
    "Initialize new configuration directory."
    os.environ['OWTF_CONF'] = "~/.owtf/configuration/framework.cfg"


    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    py_contents, yaml_contents = generate_settings(dev)

    if os.path.isfile(yaml):
        click.confirm(
            "File already exists at '%s', overwrite?" % click.format_filename(yaml), abort=True
        )

    with click.open_file(yaml, 'w') as fp:
        fp.write(yaml_contents)

    if os.path.isfile(py):
        click.confirm(
            "File already exists at '%s', overwrite?" % click.format_filename(py), abort=True
        )

    with click.open_file(py, 'w') as fp:
        fp.write(py_contents)
