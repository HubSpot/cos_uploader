'''
'''
import codecs
from copy import deepcopy
import json
import logging
import markdown
from pprint import pprint, pformat
import os
import platform
from ordereddict import OrderedDict
import re
import requests
import time
import traceback
import yaml
import sys
import time
import traceback
from uuid import uuid4
from error_reporting import report_exception



if sys.argv[0].endswith('.py'):
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger("_")
logging.getLogger("requests").setLevel(logging.WARNING)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler 
except:
    Observer = None
    LoggingEventHandler = object

from snakecharmer.propertized import Propertized, Prop
from snakecharmer.script_options import ScriptOptions, Opt
 
def main(options=None):
    options = options or Options.from_argv()
    try:
        do_main(options)
    except KeyboardInterrupt:
        print "Ctrl-c pressed, quitting"
    except Exception:
        if not options.dont_report_errors:
            report_exception()
        traceback.print_exc()
        print "Fatal error, quitting..."
        time.sleep(13)

def do_main(options):
    message = _get_startup_message()
    if message:
        print "-------------------------"
        print message
        print "-------------------------"
        raw_input("Press ctrl-c to quit, or press any key to continue ...")
    is_interactive_mode = False
    if not options.hub_id or (not options.api_key and not options.access_token):
        is_interactive_mode = True
        handle_interactive_mode(options)
    options.target_folder = options.target_folder.replace('\\', '/')
    if not os.path.isdir(options.target_folder):
        logger.fatal("The target folder (%s) does not exist" % options.target_folder)
        sys.exit(1)
    if not os.path.isdir(options.target_folder + "/files") and not os.path.isdir(options.target_folder + "/templates"):
        logger.fatal("You have neither a 'files' folder or a 'templates' folder in the target folder (%s).  There is nothing to upload.  Exiting." % options.target_folder)
        sys.exit(1)
        
    if options.action:
        _check_api_access_valid(options)
    if options.action == 'upload':
        sync_folder(options)
    elif options.action == 'watch':
        watch_folder(options)
    else:
        options.print_help()


def handle_interactive_mode(options):
    target_folder = raw_input("What folder do you want to upload? (Leave blank to use current folder \"%s\"): " % options.target_folder)
    if target_folder.strip():
        options.target_folder = target_folder.strip()
    if not os.path.isdir(options.target_folder):
        fatal("The target folder (%s) does not exist." % options.target_folder)

    config_path = options.target_folder + "/.cos-sync-config.yaml"
    config = {}
    if os.path.isfile(config_path):
        f = open(config_path, 'r')
        config = yaml.load(f) or {}
        f.close()
        options.hub_id = config.get('hub_id')
        #options.api_key = config.get('api_key')
    original_config = deepcopy(config)

    id_msg = ''
    if options.hub_id:
        id_msg = " (leave blank for default of %s)" % options.hub_id
    options.hub_id = raw_input("Enter your portal_id/hubid%s: " % id_msg).strip() or options.hub_id
    if not str(options.hub_id).isdigit():
        fatal("That is not a valid hubid")
    config['hub_id'] = options.hub_id

    if not options.access_token and not options.api_key:
        is_valid = _check_refresh_access_token(options.hub_id, config)
        if not is_valid:
            _prompt_fetch_token(options.hub_id, config)

    options.action = "watch"
    options.access_token = config.get('access_token', None)

    if original_config != config:
        if not 'api_key' in original_config and not 'access_token' in original_config:
            remember = raw_input("Remember the hubid and access token for next time? (Y/yes or no)?: " )
        else:
            remember = 'y'
        if remember.lower() in ('y', 'yes'):
            config['hub_id'] = options.hub_id
            config['api_key'] = options.api_key
            f = open(config_path, 'w')
            yaml.dump(config, f)
            f.close()

    logger.info("Uploading, then watching folder " + options.target_folder)

def _check_refresh_access_token(portal_id, config):
    if not config.get('access_token'):
        return False
    token = config.get('access_token')
    r = requests.get(api_base_url + '/content/api/v2/landing-pages?limit=1&portalId=%s&access_token=%s' % (portal_id, token), verify=False)
    if r.status_code < 300:
        return True
    if not config.get('refresh_token'):
        return False
    r = requests.post(
        'https://api.hubapi.com/hubauth/refresh',
        data={
            'refresh_token': config.get('refresh_token'),
            'client_id': config.get('client_id', ''),
            'grant_type': 'refresh_token'
            },
        verify=False
        )
    config['access_token'] = r.json()['access_token']
    return True

content_app_base_url = "https://app.hubspot.com/"
api_base_url = "https://api.hubapi.com/"
#if os.environ.get('LOCAL_DEV'):
#    content_app_base_url = "http://prodlocal.hubspotqa.com:8080"
#    api_base_url = "http://prodlocal.hubspotqa.com:8080"
                     

def _prompt_fetch_token(portal_id, config):
    secret = str(uuid4())
    raw_input("Permissions needed. Press any key to open the authorization screen in your web browser. ")
    url = content_app_base_url + "/content/%s/authorization/request?user_secret=%s" % (portal_id, secret)
    if platform.system == "Linux":
        os.system("xdg-open \"%s\"" % url)
    elif not os.name == "nt":
        os.system("open \"%s\"" % url)
    else:
        os.startfile(url)
    raw_input("Once you have granted permissions on the authorization screen, press any key to continue. ")
    result = requests.get(api_base_url + '/content/api/v2/cos-uploader/secret-to-token?user_secret=%s&portalId=%s' % (secret, portal_id), verify=False)
    result_data = result.json()
    if not result_data.get('access_token'):
        fatal("There was a fatal error trying to retrieve the access token")
    config['secret'] = secret
    config.update(result_data)
    
def _check_api_access_valid(options):
    r = requests.get(api_base_url + '/content/api/v2/landing-pages?limit=1&portalId=%s&%s' % (options.hub_id, _get_key_query(options)), verify=False)
    if r.status_code >= 300:
        fatal("The API Key or Access token you are using is not valid. If you are using a presaved token, you may need to delete your .cos-sync-config.yaml file.")
    return True
    
def _get_startup_message():
    try:
        r = requests.get(api_base_url + '/content/api/v2/cos-uploader/startup-message?portalId=327485')
        message = r.json().get('message', '')
        return message
    except:
        return ''


def _obfuscate_key(api_key):
    parts = api_key.split('-')
    return parts[0][:4] + 'x-xxxx-xxxx-x' + parts[-1][:4]

def fatal(msg):
    logger.fatal(msg)
    logger.fatal("Exiting...")
    if os.name == 'nt':
        time.sleep(7)     
    sys.exit(1)                 

def sync_folder(options):
    file_details = crawl_directory_and_load_file_details(options.target_folder)
    syncer = Syncer(options)
    for file_details in file_details:
        syncer.sync_if_changed(file_details)
    logger.info("Latest changes have been synced")
 
_force_quit = False
def watch_folder(options):
    sync_folder(options)
    event_handler = FileSyncEventHandler(options)
    observer = Observer()
    observer.schedule(event_handler, path=options.target_folder, recursive=True)
    observer.start()
    logger.info("Watching the target directory for changes. Type CTRL-C to quit.")
    try:
        while True:
            if _force_quit:
                break
            time.sleep(.2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()   

cos_types = ['files', 'templates', 'scripts', 'styles', 'pages', 'site-maps', 'blog-posts']

class FileSyncEventHandler(FileSystemEventHandler):
    def __init__(self, options):
        self.syncer = Syncer(options)
        self.options = options

    def on_modified(self, event):
        try:
            self.do_on_modified(event)
        except:
            traceback.print_exc()

    def on_created(self, event):
        if self._should_skip(event):
            return
        try:
            self.syncer.handle_file_changed(event.src_path)            
        except:
            traceback.print_exc()

    def on_moved(self, event):
        if self._should_skip(event):
            return
        try:
            self.syncer.handle_file_changed(event.dest_path)            
        except:
            traceback.print_exc()

    def _should_skip(self, event):
        if event.is_directory:
            return True
        if '.sync-history.json' in event.src_path:
            return True
        return False

    def do_on_modified(self, event):
        if self._should_skip(event):
            return
        self.syncer.handle_file_changed(event.src_path)

def crawl_directory_and_load_file_details(folder):
    all_file_details = []
    for cos_type in cos_types:
        type_folder = folder + '/' + cos_type
        for dir_path, dir_names, file_names in os.walk(type_folder):
            if dir_path.startswith('.'):
                continue
            for file_name in file_names:
                if file_name.endswith('~') or '.#' in file_name or file_name.endswith('#') or file_name.startswith('.'):
                    continue
                # Make windows use unix style paths
                dir_path = dir_path.replace('\\', '/')
                relative_path = dir_path.replace(type_folder, '').strip('/') + '/' + file_name
                relative_path = relative_path.strip('/')
                full_path = dir_path + '/' + file_name
                #logger.info("Scanning %s %s" % (cos_type, relative_path))
                try:
                    details = FileDetails().load_from_file_path(full_path, relative_path, cos_type)
                except UserError as e:
                    error(e.subject, e.message)
                    continue
                all_file_details.append(details)
    return all_file_details

class Syncer(object):
    def __init__(self, options):
        self.options = options 
        self.sync_history = self._read_sync_history()
        # Rate limit to average of 20 updates per minute

    def handle_file_changed(self, full_path):
        full_path = full_path.replace('\\', '/')
        relative_path = full_path.replace(self.options.target_folder, '').strip('/')
        cos_type = relative_path.split('/')[0]
        relative_path = '/'.join(relative_path.split('/')[1:])
        if cos_type not in cos_types:
            return
        if relative_path[-1] in ('~', '#'):
            return
        file_name = os.path.split(relative_path)[1]
        if file_name[0] == '.':
            return
        try:
            details = FileDetails().load_from_file_path(full_path, relative_path, cos_type)
            self.sync_file_details(details)
        except UserError as e:
            error(e.subject, e.message)

    def _get_last_synced_at(self, file_details):
        return self.sync_history.get(file_details.cos_type + '/' + file_details.relative_path, {}).get('last_sync_at', 0)

    def _get_last_size(self, file_details):
        return self.sync_history.get(file_details.cos_type + '/' + file_details.relative_path, {}).get('last_size', 0)
    
    def _get_object_id(self, file_details):
        return self.sync_history.get(file_details.cos_type + '/' + file_details.relative_path, {}).get('object_id', None) 

    def sync_if_changed(self, file_details):
        if file_details.last_modified_at > self._get_last_synced_at(file_details) and file_details.size != self._get_last_size(file_details):
            logger.info("File has changed: %s" % file_details.relative_path)
            self.sync_file_details(file_details)
        else:
            pass
            #logger.debug("File already up to date: %s " % file_details.relative_path)
    def sync_file_details(self, file_details):
        uploader_cls = cos_types_to_uploader[file_details.cos_type]
        uploader = uploader_cls(
            file_details=file_details,
            options=self.options,
            object_id=self._get_object_id(file_details),
            )
        logger.info("Syncing '%s/%s'" % (file_details.cos_type, file_details.relative_path))
        try:
            object_id = uploader.upload()
        except UserError as e:
            error(e.subject, e.message)
            return
        self._update_sync_history(file_details.cos_type + '/' + file_details.relative_path, object_id, file_details.size)
        self._save_sync_history()

    def _update_sync_history(self, path, object_id, size):
        self.sync_history[path] = {'id': object_id, 'last_sync_at': int(time.time() * 1000), 'last_size': size}
        

    def _save_sync_history(self):
        f = open(self.options.target_folder + '/.sync-history.json', 'w')
        history = OrderedDict(sorted(self.sync_history.items(), key=lambda t: t[0]))
        json.dump(history, f, indent=4)
        f.close()
        
    def _read_sync_history(self):
        if not os.path.isfile(self.options.target_folder + '/.sync-history.json'):
            return {}
        f = open(self.options.target_folder + '/.sync-history.json', 'r')
        try:
            result = json.load(f)
        except:
            traceback.print_exc()
            result = {}
        return result
            

default_folder = os.getcwd()
if default_folder == os.environ.get('HOME'):
    default_folder = os.path.dirname(sys.argv[0])

class Options(ScriptOptions):
    action = Opt(choices=['watch', 'upload'], help="The action. Choose 'upload' for a one time sync.  Chose 'watch' to upload and then continue to watch the directories for changes and upload all changes")
    target_folder = Opt(default=default_folder, help='The folder you want to upload.')
    hub_id = Opt(help='The hub_id or portal_id for your HubSpot account')
    api_key = Opt(help='The api key.  Get your key from https://app.hubspot.com/keys/get Only professional and enterprise portals can get a key')
    access_token = Opt(help='The OAuth access token. You can use this instead of an API Key.  Leave both api_key and access_token blank, and the cos_uploader will open your web browser to grant an access token.')
    dont_report_errors = Opt(action='store_true', help="By default, we send all errors to an error reporting service so that HubSpot engineers can fix bugs.  Include this option to disable error reporting")
    use_buffer = Opt(action='store_true', help='If set, the uploader will update the auto-save buffer rather than updating the live content')

class FileDetails(Propertized):
    last_modified_at = Prop(0)
    relative_path = Prop('')
    full_local_path = Prop('')
    metadata = Prop(dict)
    original_metadata = Prop(dict)
    content = Prop('')
    cos_type = Prop('')
    is_text_file = Prop(False)
    extension = Prop('')
    size = Prop(0)

    text_file_extensions = ['.css', '.txt', '.md', '.html', '.js', '.json', '.yaml']

    @classmethod
    def load_from_file_path(cls, file_path, relative_path, cos_type):
        stat = os.stat(file_path)
        details = cls(
            relative_path=relative_path, 
            full_local_path=file_path,
            cos_type=cos_type,
            extension=os.path.splitext(file_path)[1],
            is_text_file=os.path.splitext(file_path)[1] in cls.text_file_extensions,
            last_modified_at=int(stat.st_mtime * 1000),
            size=stat.st_size
        )
        details._hydrate_content_and_metadata()
        return details

    _json_comment_re = re.compile(r"\[hubspot-metadata]([\w\W]*?)\[end-hubspot-metadata\]")
    def _hydrate_content_and_metadata(self):
        if not self.is_text_file:
            return
        self.content = _read_unicode_file_dammit(self.full_local_path)
            
        m = self._json_comment_re.search(self.content)
        meta_json = ''
        if m:
            try:
                meta_json = '\n'.join(m.group(0).split('\n')[1:-1])
                self.metadata = json.loads(meta_json)
            except Exception as e:
                subject = 'Could not parse the metadata for %s' % self.full_local_path
                msg = str(e.message)
                the_json = '\n'.join(["%02d| %s" % (i, line) for (i, line) in enumerate(meta_json.split('\n'))])
                msg += "\nThe full JSON (with line numbers) that we tried to parse was:\n%s\n" % the_json
                msg += "Check to make sure you are double \"quoting\" everything except booleans and integers.  Make sure you have commas between items in lists in dictionaries, but no comma after the last item.\n"
                raise UserError(subject, msg)
        self.original_metadata = deepcopy(self.metadata)
        self.content = self._json_comment_re.sub('', self.content)

    def update_metadata(self, new_metadata):
        if not new_metadata:
            return
        has_changes = False
        for key, val in new_metadata.items():
            if self.metadata.get(key) != val:
                has_changes = True
        if not has_changes:
            return
        data = deepcopy(self.metadata)
        data.update(new_metadata)
        data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))        

        new_json = json.dumps(data, indent=4)
        

        org_content = _read_unicode_file_dammit(self.full_local_path)

        def replacer(m):
            parts = m.group(0).split('\n')
            return parts[0].strip() + '\n' + new_json + '\n' + parts[-1].strip()

        new_content = self._json_comment_re.sub(replacer, org_content)
        if new_content == org_content:
            return
        logger.debug("Writing new metadata")
        f = codecs.open(self.full_local_path, 'w', 'utf-8')
        f.write(new_content)
        f.close()

def _read_unicode_file_dammit(path):
    try:
        with codecs.open(path, 'r', 'utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with codecs.open(path, 'r', 'cp1250') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, 'rb') as f:
                content = f.read()
                content = unicode(content, 'utf-8', errors='ignore')
    return content 

def error(subject, msg):
    logger.error('''\n
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ERROR! %s
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        
%s

--------------------------------------------------------
    ''' % (subject, msg))
    


class UserError(Exception):
    def __init__(self, subject, message):
        self.subject = subject
        self.message = message

class BaseUploader(Propertized):
    file_details = Prop() 
    options = Prop()
    object_id = Prop()
    endpoint = ''
    api_base = 'content'

    def upload(self):
        object_id = self.get_id_from_details()
        data = self.make_json_data()
        if not object_id:
            object_id = self.lookup_id(data)
        self.check_valid(data)
        if not object_id:
            url = self.get_create_url()
            logger.debug('POST new data to %s' % url)
            r = requests.post(url, data=json.dumps(data), verify=False)
            self.object_id = r.json().get('id', None)
            if r.status_code < 300:
                logger.info('Creation successful for file %s; the new file ID is %s' % (self.file_details.relative_path, self.object_id))
        else:
            url = self.get_put_url(object_id)
            logger.debug('PUT new data to %s' % url)
            r = requests.put(url, data=json.dumps(data), verify=False)
            self.object_id = object_id
            if r.status_code < 300:
                logger.info('Update successful for file %s' % self.file_details.relative_path)
        if r.status_code > 299:
            response_content = r.content
            try:
                response_content = pformat(r.json())
            except:
                pass
            msg = '''\
Status code was: %s
Response body was:

%s
''' % (r.status_code, response_content)
            raise UserError("Problem uploading to the COS API %s " % self.file_details.relative_path, msg)
        self.process_post_upload()
        return self.object_id

    def lookup_id(self, data):
        return None

    def process_post_upload(self):
        if self.file_details.cos_type in ('templates', 'pages', 'styles', 'scripts'):
            self.file_details.update_metadata({'id': self.object_id})

    def make_json_data(self):
        data = {}
        data.update(self.file_details.metadata)
        self.hydrate_json_data(data)
        return data

    def check_valid(self, data):
        return True

    def hydrate_json_data(self, data):
        raise Exception("implement me")


    def get_create_url(self):
        return 'https://api.hubapi.com/%s/api/v2/%s?%s&portalId=%s' % (self.api_base, self.endpoint, _get_key_query(self.options), self.options.hub_id)

    def get_put_url(self, object_id):
        buffer = '/buffer'
        if not self.options.use_buffer:
            buffer = ''
        return 'https://api.hubapi.com/%s/api/v2/%s/%s%s?%s&portalId=%s' % (self.api_base, self.endpoint, object_id, buffer, _get_key_query(self.options), self.options.hub_id)

    def get_id_from_details(self):
        if self.object_id:
            return self.object_id
        elif self.file_details.metadata.get('id'):
            return self.file_details.metadata.get('id')
        else:
            return None


def _get_key_query(options):
    if options.access_token:
        return 'access_token=%s' % options.access_token.encode('utf8')
    else:
        return 'hapikey=%s' % options.api_key.encode('utf8')


    

class TemplateUploader(BaseUploader):
    endpoint = 'templates'

    def lookup_id(self, data):
        if not 'path' in data:
            return
        url = 'https://api.hubapi.com/content/api/v2/templates?path=%s&%s&portalId=%s' % (data['path'], _get_key_query(self.options), self.options.hub_id)
        r = requests.get(url, verify=False)
        result = r.json()
        if not result.get('objects', []):
            return None
        else:
            return result.get('objects')[0]['id']

    def check_valid(self, data):
        msg = ''
        is_asset = os.path.splitext(self.file_details.relative_path)[1] in ('.js', '.css')
        is_blog = data.get('category_id') == 3
        if not data.get('path') or data.get('category_id') == None or data.get('template_type') == None or (data.get('is_available_for_new_content') == None and not is_asset and not is_blog):
            msg = """\
Your template file must include a JSON metadata section.  The metadata tells us what type of content the template is associated with, whether

Here is an example metadata section:

[hubspot-metadata]
{
   "path": "custom/pages/my-folder/my-file.html",
   "category": "page",
   "creatable": false            
}
[end-hubspot-metadata]

This section can be put anywhere in the file.  It will be stripped from the file when uploaded. You can also surround the block with comment tokens to avoid errors when developing locally.

The "path" parameter controls where the template will show up in template builder.  This path can also be used in {% include %} statements by other templates.

Allowed values for "category" are:
    - email
    - blog
    - blog_post
    - blog_listing
    - asset : css or javascript files
    - include : templates that will be included by another template, as opposed to being used directly.
    - page : if you want to be able to create a new landing page or site page with this template
    - landing_page


The "creatable" parameter should be set to 'true' when you want to show this template in the new page, blog post, or email creation screen.  

You can set 'creatable' to false while you initially work on your template, and then change it to 'true' when you are ready to create a page with it.

If 'creatable' is true, then the template must have valid source content for that category.  For instance, an email template must have CAN-SPAM and unsubscribe tokens and a page template must have the {{ standard_header_includes }} and {{ standard_footer_includes }} tokens.


"""
            raise UserError("Template is not valid %s " % self.file_details.full_local_path, msg)

    def hydrate_json_data(self, data):

        category = data.get('category')
        if category in ("blog", 'blog_post'):
            data['category_id'] = 3
            data['template_type'] = 6
        elif category == 'blog_listing':
            data['category_id'] = 3
            data['template_type'] = 7
        elif category in ('page', 'landing_page', 'asset'):
            data['category_id'] = 1
            data['template_type'] = 4
        elif category == 'error_page':
            data['category_id'] = 0
            data['template_type'] = 11
        elif category == 'email':
            data['category_id'] = 2
            data['template_type'] = 2
        elif 'category' in data:
            data['category_id'] = 0
            data['template_type'] = 0

        if 'category' in data:
            del data['category']
        if data.get('category_id') == 0:
            data['is_available_for_new_content'] = False
            

        if self.file_details.relative_path.endswith('.css'):
            if not data.get('category_id'):
                data['category_id'] = 0
                data['template_type'] = 0


        if 'creatable' in data:
            data['is_available_for_new_content'] = str(data['creatable']).lower() == 'true'

        if 'is_available_for_new_content' in data:
            data['is_available_for_new_content'] = str(data['is_available_for_new_content']).lower() == 'true'
        if 'category_id' in data:
            data['category_id'] = int(data['category_id'])
        if 'template_type' in data:
            data['template_type'] = int(data['template_type'])


        if data.get('path'):
            if data['path'].count('/') == 2:
                data['path'] = 'custom/' + data['path']
            if data['path'].count('/') == 1:
                data['path'] = 'custom/' + data.get('category', 'page') + 's' + '/' + data['path']
                
        data['source'] = self.file_details.content

        
class StyleUploader(TemplateUploader):
    pass

class ScriptUploader(TemplateUploader):
    pass

class FileUploader(BaseUploader):
    endpoint = 'files'
    api_base = 'filemanager'

    def upload(self):

        files = {'files': open(self.file_details.full_local_path, 'rb')}
        folder, file_name = os.path.split(self.file_details.relative_path)
        data = {
            "file_names": file_name,
            "folder_paths": folder,
            "overwrite": "true"
         }
        logger.debug("FILE DATA %s " % data)
        object_id = self.get_id_from_details()
        if not object_id:
            object_id = self.lookup_id(data)

        if not object_id:
            url = self.get_create_url()
            logger.debug('POST URL IS %s' % url)
            r = requests.post(url, data=data, files=files, verify=False)
            logger.debug("RESULT %s " % r)
            if r.status_code < 300:
                logger.info("Creation successful for file %s.")
        else:
            url = self.get_put_url(object_id)
            logger.debug('POST URL IS %s' % url)
            r = requests.post(url, data=data, files=files, verify=False)
            if r.status_code < 300:
                logger.info("Update successful for file %s.")
            logger.debug('RESULT %s' % r)
        obj = r.json().get('objects', [{}])[0]
        logger.info("You can link to file %s at %s" % (file_name, obj.get('alt_url', '??? CDN url not found. Check the file manager.')))
        return obj['id']
            


    def lookup_id(self, data):
        alt_key = 'hub/%s/%s' % (self.options.hub_id, os.path.splitext(self.file_details.relative_path)[0])
        url = 'https://api.hubapi.com/content/api/v2/files?alt_key=%s&%s&portalId=%s' % (alt_key, _get_key_query(self.options), self.options.hub_id)
        r = requests.get(url, verify=False)
        result = r.json()
        if not result.get('objects', []):
            return None
        else:
            return result.get('objects')[0]['id']

    def hydrate_json_data(self, data):
        pass
    

class BlogPostUploader(BaseUploader):
    def hydrate_json_data(self, data):
        data['post_html'] = self.file_details.content

class PageUploader(BaseUploader):
    endpoint = 'pages'

    def lookup_id(self, data):
        url = 'https://api.hubapi.com/content/api/v2/pages?slug=%s&%s&portalId=%s' % (data['slug'], _get_key_query(self.options), self.options.hub_id)
        r = requests.get(url, verify=False)
        result = r.json()
        if not result.get('objects', []):
            return None
        else:
            return result.get('objects')[0]['id']
    def hydrate_json_data(self, data):
        if 'slug' not in data:
            data['slug'] = os.path.splitext(self.file_details.relative_path)[0]
            data['slug'] = data['slug'].lower().replace(' ', '-').replace('_', '-').replace('--', '-')
            if data['slug'].endswith('/index'):
                data['slug'] = data['slug'][:-6]
            if data['slug'] == 'index':
                data['slug'] = ''
        if 'html_title' not in data:
            data['html_title'] = os.path.split(data['slug'])[1].replace('-', ' ').replace('_', ' ').title()
        if 'name' not in data:
            data['name'] = data['slug'].replace('-', ' ').replace('_', ' ').replace('/', ' > ').title()
            if not data['name']:
                data['name'] = 'Home'
        if 'deleted_at' not in data:
            data['deleted_at'] = 0
        data['widget_containers'] = {}
        data['widgets'] = {}

        self._hydrate_widgets_via_brackets(data)
        
    _attr_re = re.compile(r'(\w+)=\"([^"]*)\"')
    def _hydrate_widgets_via_brackets(self, data):
        html = self.file_details.content
        attribute_lines = None
        current_attribute_name = None
        is_markdown = None
        container = None
        widget = None
        for line in html.split('\n'):
            attr_data = dict(self._attr_re.findall(line))
            if line.strip().startswith('[start-container'):
                container = {'widgets': []}
                data['widget_containers'][attr_data['name']] = container
            elif line.strip().startswith('[start-widget'):
                if container:
                    widget = {'type': attr_data['type'], 'body': {}}
                    container['widgets'].append(widget)
                else:
                    widget = {'body': {}}
                    data['widgets'][attr_data['name']] = widget
            elif line.strip().startswith('[start-attribute'):
                attribute_lines = []
                is_markdown = attr_data.get('is_markdown', '').lower() == 'true'
                current_attribute_name = attr_data['name']
            elif line.strip().startswith('[end-attribute]'):
                attr_html = '\n'.join(attribute_lines)
                if is_markdown:
                    attr_html = markdown.markdown(attr_html, ['fenced_code', 'toc']) 
                    attr_html = attr_html.replace('&amp;lbrace;', '&#123;')
                widget['body'][current_attribute_name] = attr_html
                attribute_lines = None
                current_attribute_name = None
                is_markdown = None
            elif line.strip().startswith('[end-widget]'):
                widget = None
            elif line.strip().startswith('[end-container]'):
                container = None
            elif attribute_lines != None:
                attribute_lines.append(line)




class SiteMapUploader(BaseUploader):
    endpoint = 'site-maps'

    def lookup_id(self, data):
        name = os.path.splitext(self.file_details.relative_path)[0]
        url = 'https://api.hubapi.com/content/api/v2/site-maps?name=%s&%s&portalId=%s' % (name, _get_key_query(self.options), self.options.hub_id)
        r = requests.get(
            url, verify=False
            )
        result = r.json()
        if not result.get('objects', []):
            return None
        else:
            return result.get('objects')[0]['id']
        
    def hydrate_json_data(self, data):
        # load all pages or slug__in?
        # get the page ids
        pages_tree = yaml.load(self.file_details.content)
        data['pages_tree'] = {
            'children': pages_tree
            }
        self._hydrate_page_ids(data['pages_tree'])

    def _hydrate_page_ids(self, tree):
        slug_to_node = {}
        all_slugs = []
        def build_dicts(node):
            slug = node.get('url')
            if slug and '//' not in slug:
                if slug.startswith('/'):
                    slug = slug[1:]
                    slug_to_node[slug] = node
                    all_slugs.append(slug)
            for child_node in node.get('children', []):
                build_dicts(child_node)
        build_dicts(tree)
        slugs_in = '&'.join(['slug__in=%s' % slug for slug in all_slugs])
        url = 'https://api.hubapi.com/content/api/v2/pages?%s&%s&portalId=%s&limit=500' % (slugs_in, _get_key_query(self.options), self.options.hub_id)
        r = requests.get(url, verify=False)
        for page in r.json().get('objects', []):
            slug_to_node[page['slug']]['page_id'] = page['id']


cos_types_to_uploader = {
    'styles': StyleUploader,
    'templates': TemplateUploader,
    'scripts': ScriptUploader,
    'files': FileUploader,
    'blog-posts': BlogPostUploader,
    'pages': PageUploader,
    'site-maps': SiteMapUploader
}            

if __name__ == '__main__':
    main()
        
