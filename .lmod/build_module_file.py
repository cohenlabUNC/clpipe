import sys 
sys.path.append("..")
import setup
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

clpipe_version = setup.VERSION
python_version = setup.PYTHON_VERSION

environment = Environment(loader=FileSystemLoader(searchpath=".lmod"))
template = environment.get_template("module_file_template.txt")
module_file_name = Path("dist") / f"{clpipe_version}.lua"

content = template.render(
    clpipe_version=clpipe_version,
    python_version=python_version
)

with open(module_file_name, mode="w") as module_file:
    module_file.write(content)