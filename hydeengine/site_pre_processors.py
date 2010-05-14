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


class ResourcePairer(object):
    @staticmethod
    def process(folder, params):
        site = settings.CONTEXT['site']
        node = params['node']

        # fetch or setup content and pairs
        content_name = params.get('name', 'media_content')
        content = site.__dict__.setdefault(content_name, {})

        variable = params.get('variable', 'media')
        rvariable = params.get('recursive_variable', 'media')
        recursive = params.get('recursive', True)

        if node.type == 'content':
            while content:
                path, node = content.popitem()
                setattr(node, variable, [])
                setattr(node, rvariable, [])
            content.update(dict([(page.url, page.node) for page in node.walk_pages()]))
        elif node.type == 'media':
            for resource in node.walk_resources():
                # strip top directories (eg. media/images/) to be able to match
                path = resource.node.fragment
                path = path[path.index('/', 1):]

                # append the resource for all matching directories
                key = variable
                node = content.get(path)
                while node is not None:
                    resources = node.__dict__.setdefault(key, [])
                    resources.append(resource)
                    resources.sort(key=lambda x: x.file.last_modified, reverse=True)

                    key = rvariable
                    node = recursive and node.parent or None


class RecursiveAttributes(object):
    """Adds recursivity base on attributes with dots"""
    def __init__(self):
        self._setup = False

    def __setattr__(self, key, value):
        parts = key.split('.', 1)
        if len(parts) == 1:
            self.__dict__[key] = value
        else:
            target = getattr(self, parts[0], None)
            if target is None:
                target = RecursiveAttributes()
                self.__dict__[parts[0]] = target

            setattr(target, parts[1], value)

    def __getattr__(self, key):
        parts = key.split('.', 1)
        try:
            if len(parts) == 1:
                return self.__dict__[key]
            else:
                return getattr(self.__dict__[parts[0]], parts[1])
        except KeyError:
            raise AttributeError('Unknown attribute: %s' % (key,))

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(['%s=%r' % (k, v) for k, v in self.__dict__.items() if not k.startswith('_')]))


class ImageMetadata(object):
    """Image metadata retriever based on PIL"""
    DEFAULT_MAPPING = {'iptc.description': 'caption'}

    # A subset of the IPTC Information Interchange Model
    # mapping extracted from:
    # http://www.iptc.org/std/IIM/
    IIM_MAPPING = {(2, 90):   'city',
                   (2, 101):  'country',
                   (2, 100):  'country_code',
                   (2, 120):  'description',
                   (2, 25):   'keywords',
                   (2, 116):  'copyright',
                   (2, 105):  'headline',
                   (2, 5):    'title',
                   (2, 15):   'category',
                   (2, 20):   'supplemental_category'}

    @staticmethod
    def process(folder, params):
        import PIL.ExifTags
        import PIL.Image
        import PIL.IptcImagePlugin

        class AttributeMapper(RecursiveAttributes):
            def __init__(self, values, mappings):
                if values is None:
                    return

                for mapping in mappings:
                    for tag, name in mapping.iteritems():
                        value = values.get(tag)
                        if value is not None:
                            setattr(self, name, value)

        # setup the mapping
        mapping = ImageMetadata.DEFAULT_MAPPING.copy()
        mapping.update(params.get('mapping', {}))

        # loop through all metadata resources
        node = params['node']
        if node.type == 'media':
            for resource in node.walk_resources():
                try:
                    image = PIL.Image.open(resource.source_file.path)
                except:
                    continue

                # not all images have exif information
                try:
                    resource.meta = RecursiveAttributes()
                    resource.meta.exif = AttributeMapper(image._getexif(), [PIL.ExifTags.TAGS, PIL.ExifTags.GPSTAGS])
                except AttributeError:
                    pass

                iptc = PIL.IptcImagePlugin.getiptcinfo(image)
                resource.meta.iptc = AttributeMapper(iptc, [ImageMetadata.IIM_MAPPING])

                # use the mapping to add easier access to some attributes
                for key, attr in mapping.items():
                    try:
                        setattr(resource.meta, attr, getattr(resource.meta, key))
                    except AttributeError:
                        pass


class ImageMetadataPyExiv2(object):
    """Image metadata retriever based on pyexiv2"""
    DEFAULT_MAPPING = {'Iptc.Application2.Caption': 'caption'}

    @staticmethod
    def process(folder, params):
        import pyexiv2

        class AttributeMapper(RecursiveAttributes):
            def __init__(self, keys, image):
                super(AttributeMapper, self).__init__()
                for key in keys:
                    setattr(self, key, image[key])
                self._setup = True

        # setup default mapping + local overrides
        mapping = ImageMetadataPyExiv2.DEFAULT_MAPPING.copy()
        mapping.update(params.get('mapping', {}))

        # loop through all media resources
        node = params['node']
        if node.type == 'media':
            for resource in node.walk_resources():
                try:
                    image = pyexiv2.Image(resource.source_file.path)
                    image.readMetadata()
                except:
                    continue

                # setup all retrieved keys in resource.meta
                keys = set(image.exifKeys() + image.iptcKeys())
                resource.meta = AttributeMapper(keys, image)

                # use the mapping to add easier access to some attributes
                for key, attr in mapping.items():
                    if key in keys:
                        setattr(resource.meta, attr, getattr(resource.meta, key))
