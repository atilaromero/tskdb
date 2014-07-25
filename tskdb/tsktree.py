#!/usr/bin/env python
from db import loaddbsqlite
from tree import Tree

class TskTree(Tree):
    def __init__(self):
        super(Tree,self).__init__()
        self.files = []

def main(path):
    meta,session = loaddbsqlite(path)
    tsk_files=meta.tbcls.tsk_files
    tree = TskTree()
    for rec in session.query(tsk_files).all():
        if rec.parent_path:
            tree[rec.parent_path.strip('/').split('/')].files.append(rec)
        else:
            tree[rec.parent_path].files.append(rec)
    return tree
        
