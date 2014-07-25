#!/usr/bin/env python
import os
from db import loaddbsqlite
from tree import Tree

class TskTree(Tree):
    def __init__(self, dbpath=None):
        super(TskTree,self).__init__()
        self.files = []
        #load db
        if dbpath != None:
            meta, session = loaddbsqlite(dbpath)
            tsk_files=meta.tbcls.tsk_files
            for rec in session.query(tsk_files).all():
                if rec.parent_path:
                    fullpath = os.path.join(rec.parent_path,rec.name)
                else:
                    fullpath = rec.name
                splitedpath = fullpath.rstrip('/').split('/')
                self[splitedpath].files.append(rec)
            self.freeze()

    def getpath(self, path):
        parts = path.rstrip('/').split('/',1)
        if len(parts) == 1: # the end
            filename = parts[0]
            if self.has_key(filename): # try to use node first
                return self[filename]
            else: # should be a file index then
                return self.files[int(filename)]
        else:
            node = self[parts[0]]
            return node.getpath(parts[1])
        

