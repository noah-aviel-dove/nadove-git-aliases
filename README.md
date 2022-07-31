# nadove-git-config

This is where I organize and develop my git aliases. This is intended purely for
personal use, so feel to copy my ideas but don't expect any sort of stability or
backwards compatibility.

# Dependencies

Implemented in pure python 3 and bash with no external libraries. The current
revision was developed using python 3.10.4 and bash 5.1.16.

Many aliases reference other aliases and thus require git>=2.20.

Developed on and for Arch Linux, probably(?) works on other linuxes but no
promises

# Installation/update/removal

Clone the repository and run

    source environment
    make install

This will add a line to `~/.bashrc` to edit `PATH` and edit the global git
configuration.

To install updates, run

    source environment
    git pull
    make update

If you never use do anything more than that, then you can remove the aliases by
running

    source environment
    make uninstall

For info on more fine-grained behavior, run

    source environment
    make help

# Disclaimer

Many of these commands make assumptions and take shortcuts that generally work
out for my own preferred workflows but are not generally applicable. The most
obvious example is the abundance of aliases that assume the existence of a
branch called `develop` which is an ancestor of the current branch. I am not
fixing this because I have no ambition of making these aliases suitable for
general use.

Proceed at your own risk and please make sure you understand the source of the
more complicated commands before running them, as some of them do things like
force-pushing.
