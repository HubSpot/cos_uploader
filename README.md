cos_syncer
==========

Installing
---------------------------------
The cos_syncer requires python 2.7.x.  Python is installed by default on Max OSX and Linux machines.  The [Windows installer is here](http://www.python.org/ftp/python/2.7.5/python-2.7.5.msi).


git clone 
cd cos_syncer
python setup.py install

Now you should be able to go to any folder from the command line and type:
>sync_to_cos.py

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