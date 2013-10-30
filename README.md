cos_syncer - ALPHA not ready for real use
=================================

Installing
---------------------------------
The cos_syncer requires python 2.7.x.  Python is installed by default on Max OSX and Linux machines.  The [Windows installer is here](http://www.python.org/ftp/python/2.7.5/python-2.7.5.msi).

Assuming you have git, python2.7, virtualenvwrapper, and pip installed:
```
git clone git@github.com:HubSpot/cos_syncer.git
mkvirtualenv cos_syncer
cd cos_syncer
pip install -r requirements.pip
mydir = $(pwd);
echo "workon cos_syncer;python "$(pwd)"/cos_syncer/sync_to_cos.py" > "/usr/local/bin/sync_to_cos"
chmod 700 /usr/local/bin/sync_to_cos
```

Now you should be able to go to the folder with your files in it from the command line and type:
``>sync_to_cos```

And you should get all the options


Basic Usage
--------------------------





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

<!--[hubspot-metadata]-->
{
    "": ""
}
<!--[end-hubspot-metadata]-->

/*[hubspot-metadata]*/

/*[end-hubspot-metadata]*/


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


<!--[hubspot-metadata]-->
{ 
"slug": "an-api-managed-blog-post"
}
<!--[end-hubspot-metadata]-->

```
