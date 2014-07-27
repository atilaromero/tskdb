#!/usr/bin/env python
import os
import sys
import errno
import plac
import functools

from fuse import FUSE, FuseOSError, Operations
import tsktree

def report(fn):
    @functools.wraps(fn)
    def wrap(*params,**kwargs):
        fc = "%s(%s)" % (fn.__name__, ', '.join(
            [a.__repr__() for a in params] +
            ["%s = %s" % (a, repr(b)) for a,b in kwargs.items()]
        ))
        print "%s called" % (fc)
        ret = fn(*params,**kwargs)
        #print "%s returned" % (fn.__name__)                                                                                                              print "%s returned %s" % (fn.__name__, ret)
        return ret
    return wrap

def reportall(cls):
    for name, val in vars(cls).items():
        if callable(val) and not name.startswith('_'):
            setattr(cls, name, report(val))
    return cls

@reportall
class TskFuse(Operations):
    def __init__(self, dbpath):
        self.tree = tsktree.TskTree(dbpath)

    def access(self, path, mode):
        return # no error, there is no access control here

    #def chmod(self, path, mode):
    #def chown(self, path, uid, gid):
    #def create(self, path, mode, fi=None):
    #def destroy(self,path):
    #def flush(self, path, fh):
    #def fsync(self, path, fdatasync, fh):
    #def fsyncdir(self,path, datasync, fh):

    def getattr(self, path, fh=None):
        return self.tree.getattr(path)

    #def getxattr(self, path, name, position=0):
    #def init(self, path):
    #def link(self, target, name):
    #def listxattr(self, path):
    #def mkdir(self, path, mode):
    #def mknod(self, path, mode, dev):

    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def opendir(self, path):
        return 0

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def readdir(self, path, fh):
        return self.tree.readdir(path)

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def release(self, path, fh):
        return os.close(fh)

    #def releasedir(self, path, fh):
    #def removexattr(self, path, name):
    #def rename(self, old, new):
    #def rmdir(self, path):
    #def setxattr(self, path, name, value, options, position=0):

    def statfs(self, path):
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    #def symlink(self, target, name):
    #def truncate(self, path, length, fh=None):
    #def unlink(self, path):
    #def utimens(self, path, times=None):
    #def write(self, path, buf, offset, fh):

def main(root, mountpoint):
    FUSE(TskFuse(root), mountpoint, foreground=True)

if __name__ == '__main__':
    plac.call(main,sys.argv[1:])
