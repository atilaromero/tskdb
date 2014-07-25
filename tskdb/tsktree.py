#!/usr/bin/env python
from db import loaddbsqlite
from tree import Tree

class TskTree(Tree):
    def __init__(self, dbpath=None):
        super(Tree,self).__init__()
        self.files = []
        if dbpath != None:
            meta, session = loaddbsqlite(dbpath)
            tsk_files=meta.tbcls.tsk_files
            for rec in session.query(tsk_files).all():
                if rec.parent_path:
                    self[rec.parent_path.strip('/').split('/')].files.append(rec)
                else: # no parent?
                    self[rec.parent_path].files.append(rec)
        
