#!/usr/bin/env python
import collections

class Tree(collections.defaultdict):
    def __init__(self):
        self.default_factory = self.__class__
    def __repr__(self):
        return str(dict(self))
    def position(self, dimensions):
        if len(dimensions) > 1:
            return Tree.position(self[dimensions[0]], dimensions[1:])
        else:
            return self[dimensions[0]]
    def checkdeep(self, checkfunc):
        if not checkfunc(self):
            return False
        for v in self.values():
            if not v.checkdeep(checkfunc):
                return False
        return True

class Compare(Tree):
    def strdates(self, x, y):
        s = [''] * 2
        if hasattr(self, 'dates'):
            s = self.dates
            s = ['{0}'.format(s[x]), '{0}'.format(s[y])]
        return ' '.join(['{0:12}'.format(x) for x in s])
    def strmd5s(self, x, y):
        s = [''] * 2
        if hasattr(self, 'md5s'):
            s = self.md5s
            s = [s[x], s[y]]
        return ' '.join([x[:4].ljust(4) for x in  s])
    def getcompare(self, field, x, y, comparefunc):
        def check(v):
            if not hasattr(v, field):
                return True #ignore, is not a leaf
            vf = getattr(v, field)
            if vf and vf[x] and vf[y]: #otherwise, ignore
                if not comparefunc(vf[x], vf[y]):
                    return False #only fails if comparison is possible
            return True
        return self.checkdeep(check)
    def getainb(self, x, y):
        def check(v):
            if not hasattr(v, 'dates'):
                return True #ignore, is not a leaf
            vf = getattr(v, 'dates')
            return  (vf[x] and vf[y]) or not vf[x]
        return self.checkdeep(check)
    def getmd5equal(self, x, y):
        return self.getcompare('md5s', x, y, lambda a, b: a == b or 'd41d8cd98f00b204e9800998ecf8427e' in (a, b))
    def getdateequal(self, x, y):
        return self.getcompare('dates', x, y, lambda a, b: a == b)
    def getdatebigger(self, x, y):
        return self.getcompare('dates', x, y, lambda a, b: a > b)
