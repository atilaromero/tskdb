#!/usr/bin/env python
import os
import datetime
import collections
from db import loaddbsqlite
from tree import Tree

def findfiles(meta,session,path):
    tsk_files=meta.tbcls.tsk_files
    for f in session.query(tsk_files)\
                    .filter(tsk_files.parent_path.startswith(path))\
                    .filter(tsk_files.meta_type==1)\
                    .filter(tsk_files.size>0)\
                    .all():
        yield f.mtime,os.path.join(f.parent_path.split(path,1)[1],f.name)

def main(path):
    meta,session = loaddbsqlite(path)
    tsk_files=meta.tbcls.tsk_files
    
    for rec in session.query(tsk_files).all():
        
