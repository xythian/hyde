import re

from django import template
from django.template import Node
from django.utils.text import normalize_newlines

register = template.Library()

class NewlineLessNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return re.sub('\s{2,}', ' ', normalize_newlines(self.nodelist.render(context)).replace('\n', ''))

@register.tag(name="newlineless")
def newlineless(parser, token):
    nodelist = parser.parse(('endnewlineless',))
    parser.delete_first_token()
    return NewlineLessNode(nodelist)

    
