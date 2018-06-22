#!/usr/bin/env python
import os
import sys
import multiprocessing.dummy
import fuse
import tskfuse
import plac
import IPython

def f(mytskfuse):
    tree = mytskfuse.tree
    IPython.embed()

def main(ddpath, dbpath, mountpoint):
    mytskfuse = tskfuse.TskFuse(ddpath, dbpath)
    t = multiprocessing.dummy.Process(target=f,args=(mytskfuse,))
    t.daemon = True
    t.start()
    fuse.FUSE(mytskfuse, mountpoint, foreground=True, allow_other=True)
    os.system('stty sane')

if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
