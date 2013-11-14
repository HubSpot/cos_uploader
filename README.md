ALPHA not ready for real use
=================================

The cos_syncer will watch the contents of a folder on your local hard drive and upload the templates and static files to the HubSpot COS every time a file child is changed.

Required before you start
----------------------------------

You must first get an API key for your HubSpot site.  These are only available for Professional and Enterprise customers.  Get your API key from here: https://app.hubspot.com/keys/get


Easy Install (Binary Distribution)
--------------------------------


#### Mac OSX 10.6+

* Open up Terminal
* Go to the folder with your assets.  Your asset folder should have one folder with "templates" and one folder with "files"

```
cd /path/to/your/asset/folder
```

* Run the following commands to download the binary and make it executable:

```
curl -L -o sync_to_cos "https://github.com/HubSpot/cos_syncer/releases/download/v0.11-alpha/sync_to_cos_osx";
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


#### Windows

Download the syncer executable from here:

https://github.com/HubSpot/cos_syncer/releases/download/v0.11-alpha/sync_to_cos.exe

Drag the downloaded file into the folder with your assets.  Double click the file to run it, give it permission when the security dialog pops up, then follow the instructions.

You can also run this executable from the command line or install it into your system path so you can run the command from any folder.



Basic Usage
--------------------------
The expected folder structure is:

* files/
* templates/

**files** contain static assets such images, javascript, css, etc.

**templates** contain files with HubSpot Markup Language.  "templates" contain tokens and tags that indicate editable areas for the end customer to edit via the UI.  Templates also contain dynamic logic.

When you run the sync, any relative links in a template file to a static file will be converted to the proper URL in our cloud content delivery network.

All files in templates must have a section in the file for metadata. The metadata is in JSON format and enclosed between two metadata tokens.

Here is an example:

```
...my template...
  </body>
</html>
<!--

[hubspot-metadata]
{
   "path": "custom/pages/my-folder/my-file.html",
   "category": "page",
   "creatable": false            
}
[end-hubspot-metadata]

-->
```

This section can be put anywhere in the file.  It will be stripped from the file when uploaded. You can also surround the block with comment tokens to avoid errors when developing locally.

The "path" parameter controls where the template will show up in template builder.  This path can also be used in {% include %} statements by other templates.

Allowed values for "category" are: email, blog, asset or include.  Set to 'page' if you want to be able to create a new landing page or site page with this template.  Set to 'asset' for css or javascript files.  Set to 'include' for any template that will be included by another template, as opposed to being used directly.

The "creatable" parameter should be set to 'true' when you want to show this template in the new page, blog post, or email creation screen.  

You can set 'creatable' to false while you initially work on your template, and then change it to 'true' when you are ready to create a page with it.

If 'creatable' is true, then the template must have valid source content for that category.  For instance, an email template must have CAN-SPAM and unsubscribe tokens and a page template must have the {{ standard_header_includes }} and {{ standard_footer_includes }} tokens.
