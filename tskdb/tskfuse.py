#!/usr/bin/env python
import os
import sys
import plac
import functools
import threading
import cmd

from fuse import FUSE, FuseOSError, Operations
import tsktree

def report(fn):
    'decorator to print each call to fn'
    @functools.wraps(fn)
    def wrap(*params,**kwargs):
        fc = "%s(%s)" % (fn.__name__, ', '.join(
            [a.__repr__() for a in params] +
            ["%s = %s" % (a, repr(b)) for a,b in kwargs.items()]
        ))
        print "%s called" % (fc)
        ret = fn(*params,**kwargs)
        print "%s returned" % (fn.__name__)
        #print "%s returned %s" % (fn.__name__, ret)
        return ret
    return wrap

def reportall(cls):
    'decorator to print each call to any function in the decorated class'
    for name, val in vars(cls).items():
        if callable(val) and not name.startswith('_'):
            setattr(cls, name, report(val))
    return cls

def _tryread(length, offset, fh):
    fh.seek(offset,0)
    chunk = fh.read(length)
    pos = fh.tell()
    if pos == offset+len(chunk): # ok
        return chunk
    else: # file is at wrong position, someone else is using it too
        # try again
        return _tryread(length, offset, fh)


@reportall # uncomment this to debug
class TskFuse(Operations):
    def __init__(self, ddpath, dbpath):
        print 'Loading db'
        self.tree = tsktree.TskTree(dbpath)
        print 'Loaded'
        self.image = open(ddpath,'r')

    def access(self, path, mode):
        return # no error, there is no access control here

    #def chmod(self, path, mode):
    #def chown(self, path, uid, gid):
    #def create(self, path, mode, fi=None):

    def destroy(self,path):
        self.image.close()

    #def flush(self, path, fh):
    #def fsync(self, path, fdatasync, fh):
    #def fsyncdir(self,path, datasync, fh):
    
    def getattr(self, path, fh=None):
        try:
            return self.tree[path].getattr()
        except IndexError:
            raise OSError(2)

    #TODO
    def getxattr(self, path, name, position=0):
        return super(TskFuse,self).getxattr(path, name, position)

    def init(self, path):
        pass

    #def link(self, target, name):

    #TODO
    def listxattr(self, path):
        pass

    #def mkdir(self, path, mode):
    #def mknod(self, path, mode, dev):
    
    def open(self, path, flags):
        return 0

    def opendir(self, path):
        return 0
        
    def read(self, path, length, offset, fh):
        try:
            layout = self.tree[path].read(length, offset)
            result = ''
            for o,l in layout:
                chunk = _tryread(l, o, self.image)
                result += chunk
                if not len(chunk) == l:
                    assert len(chunk) < l
                    return result
            return result
        except IndexError:
            raise OSError(2)

    def readdir(self, path, fh):
        try:
            return self.tree[path].readdir()
        except IndexError:
            raise OSError(2)

    #TODO
    def readlink(self, path):
        pass
    #    pathname = os.readlink(self._full_path(path))
    #    if pathname.startswith("/"):
    #        # Path name is absolute, sanitize it.
    #        return os.path.relpath(pathname, self.root)
    #    else:
    #        return pathname

    def release(self, path, fh):
        pass
    #    return os.close(fh)

    def releasedir(self, path, fh):
        pass

    #def removexattr(self, path, name):
    #def rename(self, old, new):
    #def rmdir(self, path):
    #def setxattr(self, path, name, value, options, position=0):
    
    #TODO
    def statfs(self, path):
        pass 
    #    full_path = self._full_path(path)
    #    stv = os.statvfs(full_path)
    #    return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
    #        'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
    #        'f_frsize', 'f_namemax'))

    #def symlink(self, target, name):
    #def truncate(self, path, length, fh=None):
    #def unlink(self, path):
    #def utimens(self, path, times=None):
    #def write(self, path, buf, offset, fh):
    
class Filters(cmd.Cmd):
    def __init__(self, tree):
        cmd.Cmd.__init__(self)
        self.tree = tree
        self.__prompt__ = 'Filters'

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
    import multiprocessing
    mytskfuse = TskFuse(ddpath, dbpath)
    t = multiprocessing.Process(target=FUSE, args=(mytskfuse, mountpoint), kwargs={'foreground':True})
    t.daemon = True
    t.start()
    Filters(mytskfuse.tree).cmdloop()
    t.terminate()
    
if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
