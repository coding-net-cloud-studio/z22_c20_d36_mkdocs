"""
# MkDocs Integration tests.

This is a simple integration test that builds the MkDocs
documentation against all of the builtin themes.

From the root of the MkDocs git repo, use:

    python -m mkdocs.tests.integration --help


TODOs
    - Build with different configuration options.
    - Build documentation other than just MkDocs as it is relatively simple.
"""

import logging
import os
import subprocess
import tempfile

import click

log = logging.getLogger('mkdocs')

DIR = os.path.dirname(__file__)
MKDOCS_CONFIG = os.path.abspath(os.path.join(DIR, '../../mkdocs.yml'))
MKDOCS_THEMES = ['mkdocs', 'readthedocs']
TEST_PROJECTS = os.path.abspath(os.path.join(DIR, 'integration'))


@click.command()
@click.option(
    '--output',
    help="The output directory to use when building themes",
    type=click.Path(file_okay=False, writable=True),
)
def main(output=None):
    if output is None:
        directory = tempfile.TemporaryDirectory(prefix='mkdocs_integration-')
        output = directory.name

    log.propagate = False
    stream = logging.StreamHandler()
    formatter = logging.Formatter("\033[1m\033[1;32m *** %(message)s *** \033[0m")
    stream.setFormatter(formatter)
    log.addHandler(stream)
    log.setLevel(logging.DEBUG)

    base_cmd = ['mkdocs', 'build', '-q', '-s', '--site-dir']

    log.debug("Building installed themes.")
    for theme in sorted(MKDOCS_THEMES):
        log.debug(f"Building theme: {theme}")
        project_dir = os.path.dirname(MKDOCS_CONFIG)
        out = os.path.join(output, theme)
        command = [*base_cmd, out, '--theme', theme]
        subprocess.check_call(command, cwd=project_dir)

    log.debug("Building test projects.")
    for project in os.listdir(TEST_PROJECTS):
        project_dir = os.path.join(TEST_PROJECTS, project)
        if not os.path.isdir(project_dir):
            continue
        log.debug(f"Building test project: {project}")
        out = os.path.join(output, project)
        command = [*base_cmd, out]
        subprocess.check_call(command, cwd=project_dir)

    log.debug(f"Theme and integration builds are in {output}")


if __name__ == '__main__':
    main()
