import json
import os
from threading import Thread
import time

from unittest import TestCase

from mockery.mocking import MockeryMixin, ok_, eq_

from .. import upload_to_cos
from ..upload_to_cos import Options, TemplateUploader

basic_target = os.path.dirname(__file__) + '/basic_target'
basic_sync_history_path = basic_target + "/.sync-history.json"
full_target = os.path.dirname(__file__) + '/full_target'


class TestBasic(TestCase, MockeryMixin):
    def setUp(self):
        self._clean_history()
        self._setup_mocks()

    def tearDown(self):
        self._clean_history()

    def test_sync(self):
        options = Options(action='upload', hub_id=105, api_key='noop', target_folder=basic_target)
        upload_to_cos.main(options)

    def _clean_history(self):
        if os.path.isfile(basic_sync_history_path):
            os.unlink(basic_sync_history_path)

    def _setup_mocks(self):
        options = Options(action='upload', hub_id=105, api_key='noop', target_folder=basic_target)
        def mock_get(url, *args, **kwargs):
            return MockResult(data={})
        def mock_put(url, *args, **kwargs):
            return MockResult(data={'id': 100})
        def mock_post(url, *args, **kwargs):
            if '/v2/files' in url:
                return MockResult(data={'objects':[{'id': 99}]})
            else:
                return MockResult(data={'id': 100})
            
        self.stub(upload_to_cos.requests, 'get', mock_get)
        self.stub(upload_to_cos.requests, 'put', mock_put)
        self.stub(upload_to_cos.requests, 'post', mock_post)

    def test_watch(self):
        new_path = basic_target + '/files/newfile.css'
        if os.path.isfile(new_path):
            os.unlink(new_path)
        options = Options(action='upload', hub_id=105, api_key='noop', target_folder=basic_target)
        t = AsyncMain(options)
        t.start()
        f = open(new_path, 'w')
        f.write('This is new stuff')
        f.close()
        found_change = False
        for x in range(0, 20):
            time.sleep(.1)
            if not os.path.isfile(basic_sync_history_path):
                continue
            f = open(basic_sync_history_path, 'r')
            history = json.load(f)
            if history.get('files/newfile.css', {}).get('last_sync_at', 0) > 0:
                found_change = True
                break
            f.close()
        upload_to_cos._force_quit = True
        t.join()
        ok_(found_change, 'Did not find newfile.css in the history!')
            
    def test_convert_asset_urls(self):
        uploader = TemplateUploader(options=Options(hub_id=103))
        
        for case in cases:
            out = uploader._convert_asset_urls(case['org'])
            eq_(case['exp'], out)

cases = [
    dict(
        org='''{ background-image: url(../files/asset/img/icon.png);}''',
        exp='''{ background-image: url(//cdn2.hubspot.net/hub/103/asset/img/icon.png);}'''
        ),
    dict(
        org='''{ background-image: url("../files/asset/img/icon.png");}''',
        exp='''{ background-image: url("//cdn2.hubspot.net/hub/103/asset/img/icon.png");}'''
        ),
    dict(
        org='''<video width="7"> <source src="/tutorial-from-local-html/slate-initial2.mp4" type="video/mp4"></video>''',
        exp='''<video width="7"> <source src="//cdn2.hubspot.net/hub/103/tutorial-from-local-html/slate-initial2.mp4" type="video/mp4"></video>'''
        ),
    dict(
        org='''a<link href="../files/styles/css/blog.css" />b''',
        exp='''a<link href="//cdn2.hubspot.net/hub/103/styles/css/blog.css" />b'''
        ),
    dict(
        org='''a<link rel="stylesheet" href="./asset/css/blog.css" />b''',
        exp='''a<link rel="stylesheet" href="//cdn2.hubspot.net/hub/103/asset/css/blog.css" />b'''
        ),
    dict(
        org='''a<link rel="stylesheet" href='./asset/css/blog.css' />b''',
        exp='''a<link rel="stylesheet" href='//cdn2.hubspot.net/hub/103/asset/css/blog.css' />b'''
        ),
    dict(
        org='''a<link href="asset/css/blog.css" rel="stylesheet" />b''',
        exp='''a<link href="//cdn2.hubspot.net/hub/103/asset/css/blog.css" rel="stylesheet" />b'''
        ),
    dict(
        org='''a<img src="../files/asset/img/icon.png" />b''',
        exp='''a<img src="//cdn2.hubspot.net/hub/103/asset/img/icon.png" />b'''
        ),
    dict(
        org='''a<script src="../files/asset/img/icon.js" />b''',
        exp='''a<script src="//cdn2.hubspot.net/hub/103/asset/img/icon.js" />b'''
        ),
    dict(
        org='''a<img src='../files/asset/img/icon.png' />b''',
        exp='''a<img src='//cdn2.hubspot.net/hub/103/asset/img/icon.png' />b'''
        ),
    dict(
        org='''a<img src='http://flickr.com/files/asset/img/icon.png' />b''',
        exp='''a<img src='http://flickr.com/files/asset/img/icon.png' />b'''
        ),
    dict(
        org='''a<img src='//flickr.com/files/asset/img/icon.png' />b''',
        exp='''a<img src='//flickr.com/files/asset/img/icon.png' />b'''
        ),

    
]
        

class AsyncMain(Thread):
    def __init__(self, options):
        super(AsyncMain, self).__init__()
        self.options = options

    def run(self):
        upload_to_cos.main(self.options)

class MockResult(object):
    def __init__(self, content='', data=None, status_code=200):
        self.content = content
        self.data = data
        self.status_code = status_code
    def json(self):
        if self.data != None:
            return self.data
        else:
            return json.loads(self.content)
        


class TestFull(TestCase, MockeryMixin):
    def test_main(self):
        pass



