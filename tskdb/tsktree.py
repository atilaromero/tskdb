#!/usr/bin/env python
import os
from db import loaddbsqlite
from tree import Tree

def _buildattr(metadata=None):
    if metadata:
        return {'st_atime':metadata.atime,
                'st_ctime':metadata.ctime,
                'st_gid':metadata.gid,
                'st_mode':metadata.mode,
                'st_mtime':metadata.mtime,
                'st_nlink':1,
                'st_size':metadata.size,
                'st_uid':metadata.uid,
            }
    else:
        return {'st_atime':0,
                'st_ctime':0,
                'st_gid':0,
                'st_mode':0,
                'st_mtime':0,
                'st_nlink':0,
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

    def getattr(self, path):
        parts = path.split('/',1)
        if len(parts) == 2: # more dirs to run
            if not self.has_key(parts[0]):
                raise OSError(2) # not found
            return self[parts[0]].getattr(parts[1])
        elif path and len(parts) == 1: # parts[0] == path
            # one more path to go, it can be a dir or a metadata index
            if self.has_key(path): # ok, its a dir
                return self[path].getattr('')
            else: # then it must be a metadata index
                if path.isdigit() and len(self.metadata) > int(path):
                    return _buildattr(self.metadata[int(path)])
                else:
                    raise OSError(2)
        else: #len(parts) == 0, path is empty
            mustbedir = (len(self.keys()) > 0)
            if len(self.metadata) == 0:
                # we dont have metadata for this node, fake one
                ret = _buildattr()
            if len(self.metadata) == 1: # good
                ret = _buildattr(self.metadata[0])
            else: # multiple metadata, thats a problem
                if mustbedir: # big problem
                    ret = _buildattr(self.metadata[0]) # TODO: find not deleted metadata
                else: # a file, ok thats easy
                    mustbedir = True # each metadata will be a child later
                    ret = _buildattr()
            if mustbedir:
                ret['st_mode'] |= 040000 # ISDIR
            ret['st_mode'] |= 0777 # RWX for all
            return ret

    def readdir(self, path):
        if path:
            parts = path.rstrip('/').split('/',1)
            for x in self[parts[0]].readdir(parts[1:] and parts[1] or ''):
                yield x
        else:
            if len(self.keys())>0:
                for r in self.keys():
                    yield (r, None, 0)
            elif len(self.metadata)>1:
                for r in range(len(self.metadata)):
                    yield (unicode(r), None, 0)

    def getpath(self, path):
        if len(parts) == 1: # the end
            if self.has_key(path): # try to use node first
                return self[path]
            else: # should be a file index then
                return self.metadata[int(path)]
        else:
            node = self[parts[0]]
            return node.getpath(parts[1])
        

