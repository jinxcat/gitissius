#!/usr/bin/env python
#
# Git-issues-ng
#
# Giorgos Logiotatidis <seadog@sealabs.net>
# http://www.github.com/glogiotatidis/gitissius
# http://www.gitissius.org
#
# Distributed bug tracking using git
#

import optparse
import os
import os.path
import shutil
import sys
import string

import gitshelve
import common
import commands
import properties
import database

VERSION = "0.1.6"

def usage(available_commands):
    USAGE = "Gitissius v%s\n\n" % VERSION
    USAGE += "Available commands: \n"

    for cmd in commands.available_commands:
        _cmd = commands.command[cmd]
        USAGE += "\t{0:12}: {1} (Aliases: {2})\n".\
                 format(_cmd.name,
                        _cmd.help,
                        ', '.join(_cmd.aliases) or 'None')

    return USAGE

def initialize():
    commands.import_commands()

    # check we are inside a git repo
    try:
        common.find_repo_root()
    except common.GitRepoNotFound, error:
        print error
        sys.exit(1)

    if not 'gitissius' in gitshelve.git('branch'):
        # no local gitissius branch exists
        # check if there is a remote
        if 'remotes/origin/gitissius' in gitshelve.git('branch', '-a'):
            # remote branch exists
            # create a local copy
            gitshelve.git('branch', 'gitissius', 'origin/gitissius')

        else:
            # save current branch name
            branch = gitshelve.git('name-rev', '--name-only', 'HEAD') or 'master'

            # stash changes
            try:
                gitshelve.git('stash')

            except gitshelve.GitError, error:
                pass

            # create an empty repo
            gitshelve.git('symbolic-ref', 'HEAD', 'refs/heads/gitissius')
            cwd = common.find_repo_root()
            os.unlink(os.path.join(cwd, '.git', 'index'))
            gitshelve.git('clean', '-fdx')
            gitshelve.git('commit', '--allow-empty', '-m', 'Initialization')
            gitshelve.git('checkout', branch)

            try:
                gitshelve.git('stash', 'pop')

            except gitshelve.GitError, error:
                pass

        # open the repo now, since init was done
        common.git_repo = gitshelve.open(branch='gitissius')

def close():
    common.git_repo.close()

def main():
    initialize()

    try:
        command = sys.argv[1]

    except IndexError:
        # no command given
        print usage(commands.available_commands)
        sys.exit()

    try:
        if command not in commands.command.keys():
            raise common.InvalidCommand(command)

        commands.command[command](sys.argv[2:])

    except common.InvalidCommand, e :
        print " >", "Invalid command '%s'" % e.command
        print usage(commands.available_commands)

    except common.IssueIDConflict, error:
        print " >", "Error: Conflicting IDs"
        print error

    except common.IssueIDNotFound, error:
        print " >", "Error: ID not found", error

    except KeyboardInterrupt, error:
        print "\n >", "Aborted..."

    finally:
        close()

if __name__ == '__main__':
    main()
