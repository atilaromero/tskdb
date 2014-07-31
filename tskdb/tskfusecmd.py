#!/usr/bin/env python
import os
import sys
import plac
import multiprocessing.dummy
import cmd
import fuse
import tskfuse

def useflag(tree, flagname, value):
    def f(metadata, pos):
        if metadata:
            return getattr(metadata.flags,flagname) == value
        return False
    tree.setfilter(f)

def usemetaattr(tree, attrname, value):
    def f(metadata, pos):
        if metadata:
            return getattr(metadata,attrname) == value
        return False
    tree.setfilter(f)

class Filters(cmd.Cmd):
    def __init__(self, tree):
        cmd.Cmd.__init__(self)
        self.tree = tree
        self.prompt = 'Filters$ '

    def do_metadata(self, line):
        'metadata N : force to use metadata number N when showing files'
        n = int(line)
        def f(metadata, pos):
            return pos == n
        self.tree.setfilter(f)
    
    def do_filenamecontains(self, line):
        def f(metadata, pos):
            if metadata:
                return metadata.name and metadata.name.count(line) > 0
            return False
        self.tree.setfilter(f)

    def do_alloc(self, line):
        useflag(self.tree,'alloc',1)

    def do_deleted(self, line):
        useflag(self.tree, 'alloc',0)
    
    def do_unalloc(self, line):
        useflag(self.tree, 'unalloc',1)
    
    def do_reset(self, line):
        self.tree.clearfilters()

    def do_EOF(self, line):
        sys.exit(0)


def main(ddpath, dbpath, mountpoint):
    mytskfuse = tskfuse.TskFuse(ddpath, dbpath)
    filters = Filters(mytskfuse.tree)
    t = multiprocessing.dummy.Process(target=filters.cmdloop)
    t.daemon = True
    t.start()
    fuse.FUSE(mytskfuse, mountpoint, foreground=True)
    os.system('stty sane')

if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
