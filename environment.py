import os

for var in [
    'root_dir',
    'bash_script_prefix',
    'alias_file',
    'template_file'
]:
    globals()[var] = os.environ[var]
