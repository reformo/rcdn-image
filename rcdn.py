#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-


import os
import ujson as json
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
from PIL import Image
from io import BytesIO
define("port", default=8888, help="run on the given port", type=int)
define("originals_path", default='', help="full path to original images folder", type=str)
define("buckets_path", default='', help="full path to buckets folder", type=str)


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Content-type', 'application/json')
        self.set_header('Server', 'reformo/rcdn')
        self.set_status(200, 'Success')


class ReturnImageHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Server', 'reformo/rcdn')
        self.set_status(200, 'Success')


class MainHandler(BaseHandler):
    def get(self):
        data = {"status": 200, "message": "OK"}
        output = json.dumps(data, sort_keys=True, indent=4)
        self.write(output)


class BucketHandler(ReturnImageHandler):
    def get(self, slug):
        slug_dir = os.path.dirname(slug)
        output_options_string = os.path.basename(slug_dir)
        output_options = output_options_string.split(",")
        original_slug = slug.replace(output_options_string, '')
        original_file = options.originals_path + "/" + original_slug
        output_file = options.buckets_path + "/" + slug
        output_dir = os.path.dirname(output_file)
        output = None
        size = []
        new_width = 50
        new_height = 50
        process_type = 't'
        new_adjust = 'w'
        if os.path.isfile(original_file):
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            image = Image.open(original_file)
            image.load()
            original_width, original_height = image.size
            for item in output_options:
                if item.startswith('w_'):
                    new_width = int(item.replace('w_', ''))
                if item.startswith('h_'):
                    new_height = int(item.replace('h_', ''))
                if item.startswith('crop'):
                    process_type = 'c'
                if item.startswith('a_'):
                    new_adjust = item.replace('a_', '')
            if process_type == 't':
                output = self.return_thumbnail(new_adjust, new_width, new_height, original_width, original_height, size,
                                               image, output_file)
            elif process_type == 'c':
                output = self.return_crop(image, output_file, original_width, original_height, new_width, new_height)
            self.set_header('Content-type', 'image/'+image.format)
        else:
            self.set_status(404, 'Not Found')
            output = "404/rcdn o: ("+options.originals_path+" --- "+original_slug+")" + original_file + " n:" + \
                output_file + " op:" + " ".join(output_options)
        self.write(output)

    @staticmethod
    def inner_determine_box(original_width, original_height, new_width, new_height, image):
        if original_width >= original_height:
            new_width_tmp = new_height * original_width / original_height
            image.thumbnail((new_width_tmp, new_height), Image.ANTIALIAS)
            left = int((new_width_tmp - new_width) / 2)
            right = int((new_width_tmp + new_width) / 2)
            return left, 0, right, new_height
        new_height_tmp = new_width * original_height / original_width
        image.thumbnail((new_width, new_height_tmp), Image.ANTIALIAS)
        top = int((new_height_tmp - new_height) / 2)
        bottom = int((new_height_tmp + new_height) / 2)
        return 0, top, new_width, bottom

    @staticmethod
    def return_thumbnail(new_adjust, new_width, new_height, original_width, original_height, size, image, output_file):
        o = BytesIO()
        if new_adjust == 'w':
            new_height = new_width * original_height / original_width
        elif new_adjust == 'h':
            new_width = new_height * original_width / original_height
        size.append(new_width)
        size.append(new_height)
        image.thumbnail(size, Image.ANTIALIAS)
        image.save(output_file, image.format, quality=90)
        image.save(o, image.format, quality=90)
        return o.getvalue()

    def return_crop(self, image, output_file, original_width, original_height, new_width, new_height):
        o = BytesIO()
        box = self.inner_determine_box(original_width, original_height, new_width, new_height, image)
        new_image = image.crop(box)
        new_image.load()
        new_image.save(output_file, image.format, quality=90)
        new_image.save(o, image.format, quality=90)
        return o.getvalue()


def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/bucket/(.*)", BucketHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
