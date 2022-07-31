update: scripts
	python3 update.py ~/.gitconfig ./alias.gitconfig

scripts:
	mkdir -p ./sh/cmds/
	python3 make_scripts.py ./sh/aliases.sh ./sh/cmds/
	chmod +x ./sh/cmds/_nad_git_al_*

clean:
	rm ./sh/cmds/_nad_git_al_*

test:
	python3 -m unittest test/test.py

.PHONY: update scripts clean test
