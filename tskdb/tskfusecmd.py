#!/usr/bin/env python
import os
import sys
import plac
import multiprocessing.dummy
import cmd
import fuse
import tskfuse
import tokens

def useflag(flagname, value):
    def f(metadata, pos):
        if metadata:
            return getattr(metadata.flags,flagname) == value
        return False
    return f

def usemetaattr(attrname, value):
    def f(metadata, pos):
        if metadata:
            return getattr(metadata,attrname) == value
        return False
    return f

class Filters(cmd.Cmd):
    def __init__(self, tree):
        cmd.Cmd.__init__(self)
        self.tree = tree
        self.filters = []
        self.setprompt()
        
    def setprompt(self):
        filtersnames = [x[0] for x in self.filters]
        self.prompt = '\n'.join(filtersnames+['Filters$ '])

    def addfilter(self, name, func):
        self.filters.append((name, func))
        def f(metadata, pos):
            for filt in self.filters:
                if not filt[1](metadata, pos): # all have to pass
                    return False
            return True
        self.setprompt()
        self.tree.setfilter(f)

    def do_metadata(self, line):
        'metadata N : force to use metadata number N when showing files'
        n = int(line)
        def f(metadata, pos):
            return pos == n
        self.addfilter('metadata '+line, f)
    
    def do_filenamecontains(self, line):
        def f(metadata, pos):
            if metadata:
                return metadata.name and metadata.name.upper().count(line.upper()) > 0
            return False
        self.addfilter('filenamecontains '+line, f)

    def do_parentpathcontains(self, line):
        def f(metadata, pos):
            if metadata:
                return metadata.parent_path and metadata.parent_path.upper().count(line.upper()) > 0
            return False
        self.addfilter('parentpathcontains '+line, f)

    def do_alloc(self, line):
        self.addfilter('alloc', useflag('alloc',1))

    def do_deleted(self, line):
        self.addfilter('deleted', useflag('alloc',0))
    
    def do_unalloc(self, line):
        self.addfilter('unalloc', useflag('unalloc',1))
    
    def do_reset(self, line):
        self.filters = []
        self.setprompt()
        self.tree.clearfilters()

    def do_EOF(self, line):
        sys.exit(0)

    def emptyline(self):
        pass


def main(ddpath, dbpath, mountpoint):
    mytskfuse = tskfuse.TskFuse(ddpath, dbpath)
    filters = Filters(mytskfuse.tree)
    t = multiprocessing.dummy.Process(target=filters.cmdloop)
    t.daemon = True
    t.start()
    fuse.FUSE(mytskfuse, mountpoint, foreground=True, allow_other=True)
    os.system('stty sane')

if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
