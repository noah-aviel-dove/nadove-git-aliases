update:
	python3 update.py ~/.gitconfig ./alias.gitconfig

scripts:
	python3 make_scripts.py ./sh/aliases.sh ./sh/cmds/

clean:
	rm ./sh/cmds/_nad_git_al_*

.PHONY:
	update
	clean
