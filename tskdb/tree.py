#!/usr/bin/env python
import collections

class LazyNode(dict):
    """
    A missing index will create a LazyNode, which doesn't really
    belongs to the tree until is set to some value. Then it 
    creates a new Tree node in it's place.
    """
    def __init__(self, parent, key):
        """
        parent[key] is a reference to where LazyNode should
        store a value if it ever gets set.
        """
        self.parent=parent
        self.parentkey=key
        if isinstance(parent, LazyNode):
            self.parenttype = parent.parenttype
        else:
            self.parenttype = parent.__class__
    def __missing__(self, key):
        """
        LazyNode too can have lazy childs. If a child is set, 
        it and all its parents will became real nodes.
        """
        return LazyNode(self, key)
    def __setattr__(self, attr, value):
        """
        When a value is set in a LazyNode
        """
        x = self.parenttype()
        x.attr = value
        self.parent[self.parentkey] = x
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
            return super(LazyNode,self).__getitem__(key)

class Tree(dict):
    """
    Create a tree:
        >>> t = Tree()
    
    Put a value in a node:
        >>> t[1][2][3] = 10
    
    Any unset node will return an LazyNode, detached from the tree:
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
        return LazyNode(self,key)
    __missing__.__doc__ = LazyNode.__doc__
    def __setitem__(self,key,value):
        """
        If a list is used as a key, each list item is treated 
        like a dimension: 
        [[1,2,3]] becomes [1][2][3]
        """
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
    __getitem__.__doc__ = __setitem__.__doc__

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
