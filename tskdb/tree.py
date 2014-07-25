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
        When a value is set in a LazyNode, set a real node in parent[key]
        """
        if attr in ['parent','parentkey','parenttype']:
            super(LazyNode,self).__setattr__(attr,value)
        else:
            x = self.parenttype()
            x.__setattr__(attr,value)
            self.parent[self.parentkey] = x
    def __getattr__(self, attr):
        """
        When a value is accessed in a LazyNode, create a real node in parent[key]
        """
        if attr in ['parent','parentkey','parenttype']:
            return super(LazyNode,self).__getattr__(attr)
        else:
            x = self.parenttype()
            self.parent[self.parentkey] = x
            return getattr(x,attr)
    def __setitem__(self, key, value):
        x = self.parenttype()
        x[key] = value
        self.parent[self.parentkey] = x
    __setitem__.__doc__ = __setattr__.__doc__
    def __call__(self,*args,**kwargs):
        """
        When a LazyNode is called, it behave like a call to Tree(), creating a new instance.
        This is only useful when subclassing Tree.
        Example:
        >>> class Position(Tree):
        ...     def __init__(self,x=None,y=None):
        ...         self.x = x
        ...         self.y = y
        ...     def __repr__(self):
        ...         return 'x=%s,y=%s,%s'%(self.x,self.y,dict.__repr__(self))

        >>> p = Position()

        >>> p[1][2](10,20)

        >>> p
        x=None,y=None,{1: x=None,y=None,{2: x=10,y=20,{}}}
        """
        x = self.parenttype(*args,**kwargs)
        self.parent[self.parentkey] = x
    def __getitem__(self,key):
        if isinstance(key,list): #convert [[1,2,3]] to [1][2][3] by recursion
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
        self.__frozen__ = False

    def freeze(self):
        """Disable automatic node creation"""
        self.__frozen__ = True
        
        for k in self.keys():
            self[k].freeze()

    def __missing__(self,key):
        if self.__frozen__:
            raise IndexError(key)
        else:
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

if __name__ == "__main__":
    import doctest
    doctest.testmod()
