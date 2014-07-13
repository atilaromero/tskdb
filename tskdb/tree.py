#!/usr/bin/env python
import collections

class EmptyNode(dict):
    def __init__(self, parent, key):
        self.parent=parent
        self.parentkey=key
        if isinstance(parent, EmptyNode):
            self.parenttype = parent.parenttype
        else:
            self.parenttype = parent.__class__
    def __missing__(self, key):
        return EmptyNode(self, key)
    def __setitem__(self, key, value):
        x = self.parenttype()
        x[key] = value
        self.parent[self.parentkey] = x
    def __call__(self,*args,**kwargs):
        x = self.parenttype(*args,**kwargs)
        self.parent[self.parentkey] = x
    def __getitem__(self,key):
        if isinstance(key,list):
            if len(key) > 1:
                return self[key[0]][key[1:]]
            else:
                return self[key[0]]
        else:
            return super(EmptyNode,self).__getitem__(key)

class Tree(dict):
    """
    Create a tree:
        >>> t = Tree()
    
    Put a value in a node:
        >>> t[1][2][3] = 10
    
    Any unset node will return an EmptyNode, detached from the tree:
        >>> t[4][5][6]       
        {}
    
    See, no trace of t[4][5][6] in t:
        >>> t
        {1: {2: {3: 10}}}
    
    You may use t[[1,2,3]] instead of t[1][2][3]:
        >>> t[[1,2,3]] == t[1][2][3]
        True
    
    Another example:
        >>> t = Tree()
        >>> t['dir1/dir2/dir3'.split('/')] = 100
        >>> t
        {'dir1': {'dir2': {'dir3': 100}}}
    """
    def __init__(self,*args,**kwargs):
        super(Tree,self).__init__(*args,**kwargs)
    def __missing__(self,key):
        return EmptyNode(self,key)
    def __setitem__(self,key,value):
        if isinstance(key,list):
            if len(key) > 1:
                self[key[0]][key[1:]] = value
            else:
                self[key[0]] = value
        else:
            return super(Tree,self).__setitem__(key,value)
    def __getitem__(self,key):
        if isinstance(key,list):
            if len(key) > 1:
                return self[key[0]][key[1:]]
            else:
                return self[key[0]]
        else:
            return super(Tree,self).__getitem__(key)
    def checkdeep(self, checkfunc):
        if not checkfunc(self):
            return False
        for v in self.values():
            if not v.checkdeep(checkfunc):
                return False
        return True

class DefaultDict(Tree,collections.defaultdict):
    def __init__(self,*args,**kwargs):
        super(DefaultDict,self).__init__(*args,**kwargs)
        self.default_factory = self.__class__
    def __repr__(self):
        return str(dict(self))

class Compare(Tree):
    def strdates(self, *args):
        s = [''] * len(args)
        if hasattr(self, 'dates'):
            s = self.dates
            s = ['{0}'.format(s[x]) for x in args]
        return ' '.join(['{0:12}'.format(x) for x in s])
    def strmd5s(self, *args):
        s = [''] * len(args)
        if hasattr(self, 'md5s'):
            s = self.md5s
            s = [s[x] for x in args]
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

if __name__ == "__main__":
    import doctest
    doctest.testmod()
