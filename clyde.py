import os
import sys                                                                                     
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import simplejson as json
import unicodedata

from tornado.options import define, options                                                   
from django.conf import settings         
from hydeengine import setup_env
from hydeengine.siteinfo import SiteInfo 
from hydeengine.file_system import File, Folder

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/site/([^/]+)", SiteHandler),           
            (r"/site/([^/]+/files)", FilesJSONHandler),
            (r"/site/([^/]+/content)", ContentHandler),                       
             
        ]
        opts = dict(                               
            static_path = os.path.join(os.path.dirname(__file__), "clydeweb/media"),        
            sites = dict(
               mysite = "/Users/lakshmivyas/mysite"
            )
        )
        tornado.web.Application.__init__(self, handlers, **opts)


class BaseHandler(tornado.web.RequestHandler):
    def get(self, site):
        if not hasattr(settings, 'siteinfo'):
            setup_env('/Users/lakshmivyas/mysite')
            setattr(settings, 'siteinfo', {})  
            
        if not site in settings.siteinfo:                
            siteinfo = SiteInfo(settings, '/Users/lakshmivyas/mysite')
            siteinfo.refresh()               
            settings.siteinfo[site] = siteinfo

        self.siteinfo = settings.siteinfo[site]
        
        self.doget(site)
    
    def doget(self, site): abstract

class FilesJSONHandler(BaseHandler):
    def doget(self, site):           
        d = self.siteinfo.content_node.simple_dict     
        def jsresource(resource):
            return dict(
                    attributes = dict(
                        tooltip=resource['path'], rel='file'),
                    data = dict(title=resource['name'])
            )
        def jsnode(node):
            children = [jsresource(resource) for resource in
                            node['resources']]                           
            children.append([jsnode(child_node)                 
                                for child_node in node['nodes']])  
            return dict(
                    attributes = dict(tooltip=node['path']),
                    data = dict(
                        title=node['name'],attributes=dict()),                
                    children=children
                    )
        jsdict = jsnode(d)           
        jsdict['state'] = 'open'
        jsonobj = json.dumps(jsdict)    
        self.set_header("Content-Type", "application/json")
        self.write(jsonobj)
        

class ContentHandler(BaseHandler):
    def doget(self, site): 
         path = self.get_argument("path", None)
         if not path: return
         f = File(self.siteinfo.folder.child(path))
         self.write(f.read_all())           
        
class SiteHandler(tornado.web.RequestHandler):
    def get(self, site):
        self.render("clydeweb/templates/site.html", site=site)
            

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
        