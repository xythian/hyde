import os
import sys                                                                                     
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import simplejson as json
import unicodedata
import yaml

from tornado.options import define, options                                                   
from django.conf import settings         
from hydeengine import setup_env
from hydeengine.siteinfo import SiteInfo 
from hydeengine.file_system import File, Folder

define("port", default=8888, help="run on the given port", type=int)
define("sites", default="sites.yaml", help="yaml file with site definition", type=str)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/sites", SitesJSONHandler),           
            (r"/site/([^/]+)", SiteHandler),           
            (r"/site/([^/]+)/files", FilesJSONHandler),
            (r"/site/([^/]+)/content", ContentHandler),
            (r"/site/([^/]+)/content/save", SaveHandler),                                   
             
        ]   
        sites = yaml.load(File(options.sites).read_all())
        opts = dict(                               
            static_path = File(__file__).parent.child("clydeweb/media"),                    
            sites = sites
        )
        tornado.web.Application.__init__(self, handlers, **opts)


class BaseHandler(tornado.web.RequestHandler): 

    def init_site(self, site):
        if not site in self.settings['sites']: 
            raise Exception("Site [%s] is not configured." % (site, ))
            
        self.site_path = self.settings['sites'][site]["path"]    
        if not hasattr(settings, 'siteinfo'):
            setup_env(self.site_path)
            setattr(settings, 'siteinfo', {})  
            
        if not site in settings.siteinfo:                
            self.siteinfo = SiteInfo(settings, self.site_path)
            self.siteinfo.refresh()               
            settings.siteinfo[site] = self.siteinfo   
        else:
            self.siteinfo = settings.siteinfo[site]    
    
    def get(self, site):
        self.init_site(site)
        self.doget(site)
    
    def doget(self, site): abstract           
    
    def post(self, site):  
        self.init_site(site)
        self.dopost(site)
    
    def dopost(self, site): abstract

class SitesJSONHandler(tornado.web.RequestHandler):
    def get(self):
        d = self.settings['sites']
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(sorted(d.keys())))

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

class SaveHandler(BaseHandler):    
    def dopost(self, site):
        path = self.get_argument("path", None)
        if not path: return                        
        content = self.get_argument("content", None)
        f = File(self.siteinfo.folder.child(path)) 
        f.write(content)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()