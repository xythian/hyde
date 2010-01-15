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

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/site/([^/]+)", SiteHandler),           
            (r"/site/([^/]+/files)", FilesJSONHandler),           
             
        ]
        opts = dict(                               
            static_path = os.path.join(os.path.dirname(__file__), "clydeweb/media"),        
            sites = dict(
               mysite = "/Users/lakshmivyas/mysite"
            )
        )
        tornado.web.Application.__init__(self, handlers, **opts)

class FilesJSONHandler(tornado.web.RequestHandler):
    def get(self, site):
        if not hasattr(settings, 'siteinfo'):
            setup_env('/Users/lakshmivyas/mysite')
            siteinfo = SiteInfo(settings, '/Users/lakshmivyas/mysite')
            siteinfo.refresh()                                        
            setattr(settings, 'siteinfo', siteinfo)
        else:
            siteinfo = settings.siteinfo    
        d = siteinfo.content_node.simple_dict     
        def jsresource(resource):
            return dict(
                    attributes = dict(tooltip=resource['path'], rel='file'),
                    data = resource['name']
            )
        def jsnode(node):  
            children = [jsresource(resource) for resource in
                            node['resources']]                           
            children.append([jsnode(child_node)                 
                                for child_node in node['nodes']])
            return dict(
                    attributes = dict(tooltip=node['path']),
                    data = node['name'],                
                    children=children,
                    state='open'
                    )
        jsdict = jsnode(d)
        jsonobj = json.dumps(jsdict)    
        self.set_header("Content-Type", "application/json")
        self.write(jsonobj)                                   
        
class SiteHandler(tornado.web.RequestHandler):
    def get(self, site):
        self.render("clydeweb/templates/site.html")
            

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
        