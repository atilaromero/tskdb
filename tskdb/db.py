#!/usr/bin/env python
import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

Base = sqlalchemy.ext.declarative.declarative_base()

def loaddbsqlite(path):
    return loaddb('sqlite:///%s'%path)

def loaddb(constr):
    def get_model(metadata, tablename, modelname=None):
        if modelname is None:
            modelname = str(tablename)
        cls = type(modelname, (Base,), dict(
            __table__=sqlalchemy.Table(tablename, metadata, autoload=True)
        ))
        return cls
    engine = sqlalchemy.create_engine(constr)
    meta = sqlalchemy.MetaData(bind=engine)
    session = sqlalchemy.orm.create_session(bind=engine)
    class Empty:
        pass
    meta.tbcls = Empty()
    meta.reflect(bind=engine)
    for t in meta.tables.keys():
        cls = None
        try:
            cls = get_model(meta, t)
        except:
            pass
        setattr(meta.tbcls, t, cls)
    return meta, session

