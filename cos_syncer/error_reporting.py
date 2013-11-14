import os
import sys

import requests
from urlparse import urlsplit
from pprint import pformat
from uuid import uuid4

from raven import Client
from raven.transport.base import HTTPTransport

def report_exception(): 
    # We don't report if this is run from a test, run directly from the source
    if 'nosetests' in sys.argv[0]:
        return
    if sys.argv[0].endswith('.py'):
        return
    # We use raven to get the stack trace information, but we don't use raven to report
    # because client side, reporting doesn't work python.  We need to include a secret
    # key to report, and we don't want to check in the secret key to github
    Client.register_scheme('custom+https', CustomTransport)
    client = Client('custom+https://noop@app.getsentry.com/666')
    data = client.build_msg('raven.events.Exception')
    requests.post(
        "https://forms.hubspot.com/uploads/form/v2/327485/2310f9fb-c192-40f2-b191-bf0b1cbcff76",
        headers={
            'content_type': "application/x-www-form-urlencoded"
            },
        data={"email": str(uuid4()) + ".formreporting@hubspot.com", "json_blob": pformat(data)}
        )


        
class CustomTransport(HTTPTransport):
    scheme = 'custom+https'

    def __init__(self, parsed_url):
        super(CustomTransport, self).__init__(parsed_url)
        self._url = self._url.split('+', 1)[-1]


    def compute_scope(self, url, scope):
        url = urlsplit(self._url)
        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]
        if not all([project, url.username]):
            raise ValueError('Invalid Sentry DSN: %r' % url.geturl())

        netloc = url.hostname
        netloc += ':%s' % 443

        server = '%s://%s%s/api/%s/store/' % (
            url.scheme, netloc, path, project)
        scope.update({
            'SENTRY_SERVERS': [server],
            'SENTRY_PROJECT': project,
            'SENTRY_PUBLIC_KEY': url.username,
            'SENTRY_SECRET_KEY': '',
        })
        return scope
    

