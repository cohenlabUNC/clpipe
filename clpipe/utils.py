import click
import os
@click.command()
@click.argument('subjects', nargs=-1, required=False, default=None)
@click.option('-config_file', type=click.Path(exists=True, dir_okay=False, file_okay=True), default=None,
              help='Use a given configuration file. If left blank, uses the default config file, requiring definition of BIDS, working and output directories.')
@click.option('-submit', is_flag=True, default=False, help='Flag to submit commands to the HPC')
@click.option('-debug', is_flag=True, help='Flag to enable detailed error messages and traceback')
def test_func( config_file=None, subjects=None,submit=False, debug=False):
    ctx = click.get_current_context()
    ctx.info_name


def command_log(config):
    ctx = click.get_current_context()
    print(ctx.info_name)
    print(os.getlogin())

def parse_cli_subjects(directory_path: str, subjects:list=None):
    if not subjects:
        sublist = [o.replace('sub-', '') for o in os.listdir(directory_path)
                   if os.path.isdir(os.path.join(directory_path, o)) and 'sub-' in o]
    else:
        sublist = subjects

    return sublist
