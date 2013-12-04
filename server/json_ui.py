# import sqlalchemy
import database as db
import cherrypy
# from sqlalchemy import or_, and_
from cgi import escape as html_escape
import re


class JSONAPI(object):

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def callstacks(self, id=None, **kwargs):
        if id:
            item = db.session.query(db.CallStack).get(id)
            if item:
                return item.to_dict()
            else:
                raise cherrypy.NotFound
        else:
            results = db.session.query(db.CallStack)
            return [item.to_dict() for item in results.all()]


    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sqlstatements(self, id=None, **kwargs):
        if id:
            item = db.session.query(db.SQLStatement).get(id)
            if item:
                response = item.to_dict()
                response['stack'] = item._stack()
                # substitute args
                sql_string = str(response['sql'])
                for arg in response['args']:
                    sql_string = re.sub(r'\?', arg, sql_string, 1)
                response['sql'] = sql_string
                return response
            else:
                raise cherrypy.NotFound
        else:
            results = db.session.query(db.SQLStatement)
            return [item.to_dict() for item in results.all()]

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sqlstackitems(self, id=None, **kwargs):
        if id:
            return db.session.query(db.SQLStackItem).get(id).to_dict()
        else:
            results = db.session.query(db.SQLStackItem)
            return [item.to_dict() for item in results.all()]

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def fileaccesses(self, id=None, **kwargs):
        if id:
            return db.session.query(db.FileAccess).get(id).to_dict()
        else:
            results = db.session.query(db.FileAccess)
            return [item.to_dict() for item in results.all()]
            
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def metadata(self, id=None, **kwargs):
        results_list = []
        if 'get_keys' in kwargs:
            key_list_dicts = db.session.query(db.MetaData.key).distinct().all()
            results_list = [key_dict[0] for key_dict in key_list_dicts]
        else:
            metadata_list = db.session.query(db.MetaData).filter_by(**kwargs).all()
            results_list = [metadata.__dict__['value'] for metadata in metadata_list]
        
        results_list.sort(key=unicode.lower)
        return results_list
