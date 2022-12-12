update: scripts
	python3 nadove_git_config.py --create

scripts:
	mkdir -p ./sh/cmds/
	python3 make_scripts.py ./sh/aliases.sh ./sh/cmds/
	chmod +x ./sh/cmds/"$$bash_script_prefix"*

clean:
	rm "$$alias_file" ./sh/cmds/"$$bash_script_prefix"*

install: update
	python3 nadove_git_config.py --include
	echo export 'PATH=$$PATH':"$$root_dir"/sh/cmds/ >>~/.bashrc

uninstall:
	python3 nadove_git_config.py --exclude

test:
	python3 -m unittest test/test.py

help:
	python3 nadove_git_config.py --help

.PHONY: update scripts clean install uninstall test help
