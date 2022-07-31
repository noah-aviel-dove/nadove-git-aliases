global: scripts
	python3 nadove_git_config.py --global

local: scripts

system:

aliases:
	python3 nadove_git_config.py --local

scripts:
	mkdir -p ./sh/cmds/
	python3 make_scripts.py ./sh/aliases.sh ./sh/cmds/
	chmod +x ./sh/cmds/_nad_git_al_*

clean:
	rm alias.gitconfig ./sh/cmds/_nad_git_al_*

.PHONY: aliases scripts clean
