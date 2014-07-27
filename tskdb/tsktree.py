#!/usr/bin/env python
import os
from db import loaddbsqlite
from tree import Tree

def _buildattr(metadata=None):
    if metadata:
        return {'st_atime':metadata.atime or 0,
                'st_ctime':metadata.ctime or 0,
                'st_gid':metadata.gid or 0,
                'st_mode':metadata.mode or 0,
                'st_mtime':metadata.mtime or 0,
                'st_nlink':1,
                'st_size':metadata.size or 0,
                'st_uid':metadata.uid or 0,
            }
    else:
        return {'st_atime':0,
                'st_ctime':0,
                'st_gid':0,
                'st_mode':0,
                'st_mtime':0,
                'st_nlink':1,
                'st_size':0,
                'st_uid':0,
            }
        
class TskTree(Tree):
    def __init__(self, dbpath=None):
        super(TskTree,self).__init__()
        self.metadata = []
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
                self[splitedpath].metadata.append(rec)
            self.freeze()

    def __getitem__(self, key):
        if (isinstance(key,str) or isinstance(key,unicode)) and key.count('/') > 0:
            parts = key.rstrip('/').split('/')
            return super(TskTree,self).__getitem__(parts)
        else:
            return super(TskTree,self).__getitem__(key)

    def getattr(self):
        if len(self.metadata) == 0:
                # we dont have metadata for this node, fake one
            ret = _buildattr()
        else: # len(self.metadata) >= 1:
            ret = _buildattr(self.metadata[0]) # picking first metadata found !!!!
        print [ret,]
        mustbedir = (len(self.keys()) > 0)
        if mustbedir:
            ret['st_mode'] |= 040000 # IFDIR
        if (ret['st_mode'] & 0170000) == 0: # file type not set
            ret['st_mode'] |= 0100000 # IFREG
        ret['st_mode'] |= 0777 # RWX for all
        return ret

    def readdir(self):
        if len(self.keys())>0:
            for r in self.keys():
                yield (r, None, 0)
        elif len(self.metadata)>1:
            for r in range(len(self.metadata)):
                yield (unicode(r), None, 0)

