#!/usr/bin/env python
import sys
import plac
import multiprocessing.dummy
import cmd
import fuse
import tskfuse

class Filters(cmd.Cmd):
    def __init__(self, tree):
        cmd.Cmd.__init__(self)
        self.tree = tree
        self.prompt = 'Filters'

    def do_alloc(self, line):
        def f(node):
            m = node.pickmetadata()
            if m:
                return m.flags.alloc == 1
            return False
        self.tree.setfilter(f)
    
    def do_unalloc(self, line):
        def f(node):
            m = node.pickmetadata()
            if m:
                return m.flags.unalloc == 1
            return False
        self.tree.setfilter(f)
    
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

if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
