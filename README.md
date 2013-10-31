cos_syncer - ALPHA not ready for real use
=================================

Easy Installation From the Binaries
--------------------------------------------

### Mac OSX 10.6+

* Open up Terminal
* Go to the folder with your assets.  Your asset folder should have one folder with "templates" and one folder with "files"

```
cd /path/to/your/asset/folder
```

* Run the following command to download the binary and make it executable:

```
wget https://github.com/HubSpot/cos_syncer/releases/download/v0.10-alpha/sync_to_cos_osx -O sync_to_cos; 
chmod 700 sync_to_cos;
```

* Now you can run the sync watcher:

```
./sync_to_cos
```

To get all the options, run with the help flag:

```
./sync_to_cos -h
```                


### Windows





Installing from the Source
---------------------------------
The cos_syncer requires python 2.7.x.  Python is installed by default on Max OSX and Linux machines.  The [Windows installer is here](http://www.python.org/ftp/python/2.7.5/python-2.7.5.msi).

Assuming you have git, python2.7, virtualenvwrapper, and pip installed:
```bash
# Clone the git repo to get the code
git clone git@github.com:HubSpot/cos_syncer.git
# Go into the main code directory
cd cos_syncer
# Create a python virtualenv in order to hold dependencies
mkvirtualenv cos_syncer
# install dependencies
pip install -r requirements.pip
# create a wrapper script that will run from the command line anywhere
echo "source $WORKON_HOME/cos_syncer/bin/activate;python "$(pwd)'/cos_syncer/sync_to_cos.py $*' > "/usr/local/bin/sync_to_cos"
# give the wrapper script execute privileges
chmod 700 /usr/local/bin/sync_to_cos
```

Now you should be able to go to the folder with your files in it from the command line.  Enter the following command, and the help will be printed out:
```
>sync_to_cos
``` 

To use the sync script with your portal, go to https://app.hubspot.com/keys/get and get an API key for your portal.

Then cd to the folder with your files and run:
```>sync_to_cos --hub-id=(your hubid or portalid) --api-key=(your api key) -a sync```


Basic Usage
--------------------------
The expected folder structure is:

* files/
* templates/

**files** contain static assets such images, javascript, css, etc.

**templates** contain files with HubSpot Markup Language.  "templates" contain tokens and tags that indicate editable areas for the end customer to edit via the UI.  Templates also contain dynamic logic.

When you run the sync, any relative links in a template file to a static file will be converted to the proper URL in our cloud content delivery network.



Advanced Usage
----------------------------------------

A python script for syncing a file tree to the HubSpot COS


Expected folder structure:

files/
templates/
scripts/
styles/
blog-posts/
pages/
site-maps/

**files** are static assets that should not change much.  This would include images, vendor libraries such as jquery ui, documents, etc.  

**templates** are .html template files that can be used to create pages.

**scripts** are javascript files that you will be changing more often.

**styles** are css files that you will be changing more often.

**pages** are actual publishable pages.  These require their own special syntax to work properly.

**site-maps**

**blog-posts** These can be written in .html or markdown.  Metadata is required.


Add metadata to any .html, .js, or .css file, by putting JSON inside a comment.  The JSON is identicaly to the allowed JSON for a PUT or POST request in the relevant REST API.  The comment will be stripped during the upload process.

&lt;!--[hubspot-metadata]
{
    "": ""
}
[end-hubspot-metadata]--&gt;

/\*[hubspot-metadata]

[end-hubspot-metadata]\*/


Don't like the default file structure?

If you include type metadata in your file, we will treat it as that type.
{
   "cos_type": "style"
}

**Page Syntax**

```html
<div id="page_content">
<div widget_name="">
    <div attribute_name="html">

    </div>
</div>
<div container_name="left_column">
     <div widget_type="rich_text">
          <div attribute_name="html">
This is the HTML that will be stored in the widget.
Relative URLS
          </div>
     </div>
</div>
</div>
```




**Blog post syntax**

Markdown version:
```
The title of the blog post
=========================


<!--[hubspot-metadata]
{ 
"slug": "an-api-managed-blog-post"
}
[end-hubspot-metadata]-->

```
