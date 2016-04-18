# Image Service

A simple service written in Python that is used to resize images that have been already uploaded to server
using method that user preferred (FTP, CMS, Member's upload etc.)

### Installation

```
$ pip3 install -r pip.install
```

### Usage

```
$ python3.5 ./rcdn.py --port=8000 --originals_path=/var/www --buckets_path=/tmp/buckets
```


### Upstart Service

Create a configuration file  **/etc/init/rcdn_image.conf** with following codes

```
description "RCDN Image Service"
author "mehmet@mkorkmaz.com"

start on runlevel [2345]
stop on runlevel [!2345]

respawn
setuid nobody
setgid nogroup

exec python3.4 /home/user/rcdn.py --port=8000 --originals_path=/home/rcdn/storage --buckets_path=/tmp/rcdn/buckets
```

**Service management**

```
sudo service rcdn_image start|stop|restart
```

**Server configuration recommendations**

We use this script behind an Nginx reverse proxy that serves behind Cloudflare Network.
So, once a request hits Nginx, second time Cloudlare will serve the resized file.

Define virtual host's root as --buckets_path without bucket name at the end.
In the example above virtual host's root is /tmp/rcdn).

We prefer /tmp because once a resized image created and started to be served by Cloudflare
it won't be needed on the server, so, since /tmp folder's content is deleted regularly we don't have to manage
that folder's content

With the configuration mentioned above you can use any VPS that has small resources (like 1GB RAM anf 1 CPU).

```
server {
        listen   80;
        listen   [::]:80;
        root /tmp/rcdn;
        server_name resizer.rcdn.co;
        location / {
                try_files $uri $uri/ @resizer;
        }
        ## rcdn image service
        location @resizer {
                proxy_pass http://127.0.0.1:8000;
        }
}
```


### Get resized and/or cropped image

Resize and crop
```
http://127.0.0.1:8000/bucket/bucket_name/w_200,h_300,crop/test_image.jpg
```

Resize only
```
http://127.0.0.1:8000/bucket/bucket_name/w_200,h_300/test_image.jpg
```