# -*- coding: utf-8 -*-
"""
PRE PROCESSORS

Can be launched before the parsing of each templates and
after the loading of site info.
"""

from __future__ import with_statement

import codecs
import operator
import os
import urllib

from django.conf import settings
from django.template.loader import render_to_string

import hydeengine.url as url


class Category:
    def __init__(self):
        self.posts = []
        self.feed_url = None
        self.archive_url = None

    @property
    def posts(self):
        return self.posts

    @property
    def feed_url(self):
        return self.feed_url

    @property
    def archive_url(self):
        return self.archive_url


class CategoriesManager:
    """Category Manager

    Fetch the category(ies) from every post under the given node
    and creates a reference on them in CONTEXT and the node.
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']
        node = params['node']
        categories = {}
        for post in node.walk_pages():
            if not getattr(post, 'categories', None):
                continue

            for category_name in post.categories:
                category = categories.setdefault(category_name, Category())
                category.posts.append(post)
                category.posts.sort(key=operator.attrgetter('created'),
                                    reverse=True)

        context['categories'] = categories
        node.categories = categories


class CategoriesArchiveGenerator:
    @staticmethod
    def process(folder, params):
        node = params['node']
        categories = getattr(node, 'categories', None)
        if categories is None:
            raise ValueError("No categories member on node %s" % (node))

        # define output folder (customizable)
        relative_folder = output_folder = 'archives'
        if params.get('output_folder'):
            relative_folder = output_folder = params['output_folder']

        output_folder = os.path.join(settings.TMP_DIR, folder.name, output_folder)
        if not os.path.isdir(output_folder):
            os.makedirs(output_folder)

        # fetching default archive template
        try:
            template = os.path.join(settings.LAYOUT_DIR, params['template'])
        except KeyError:
            raise ValueError("No template reference in CategoriesArchiveGenerator's settings")

        # setup urls for all categories
        for name, category in categories.iteritems():
            archive_resource = urllib.quote_plus(name) + '.html'
            category.archive_url = "/%s/%s" % (folder.name, "%s/%s" % (relative_folder, archive_resource))

            # TODO break out checks from siteinfo.py
            if settings.GENERATE_CLEAN_URLS:
                category.archive_url = url.clean_url(category.archive_url)
                if settings.APPEND_SLASH:
                    category.archive_url += '/'

        # write all files
        for category_name, category_obj in categories.iteritems():
            settings.CONTEXT.update({'category': category_name,
                                     'posts': category_obj.posts,
                                     'categories': categories})

            archive_resource = urllib.quote_plus(category_name) + '.html'
            output = render_to_string(template, settings.CONTEXT)
            output_filename = os.path.join(output_folder, archive_resource)
            with codecs.open(output_filename, "w", "utf-8") as file:
                file.write(output)


class NodeInjector(object):
    """Node Injector

    Finds the node that represents the given path and injects it with the given
    variable name into all the posts contained in the current node.
    """
    @staticmethod
    def process(folder, params):
        context = settings.CONTEXT
        site = context['site']
        node = params['node']
        try:
            varName = params['variable']
            path = params['path']
            params['injections'] = { varName: path }
        except KeyError:
            pass

        for varName, path in params['injections'].iteritems():
            nodeFromPathFragment = site.find_node(site.folder.parent.child_folder(path))
            if not nodeFromPathFragment:
                continue
            for post in node.walk_pages():
                setattr(post, varName, nodeFromPathFragment)
