Running the sync from a locally modifiable version
-----------------------------------

These instructions allow you to get the source of the syncer, and run it locally from the source code version, so you can make changes and use the program from your changed version.

You will need:
* python 2.7.x Python is installed by default on Max OSX and Linux machines.  The [Windows installer is here](http://www.python.org/ftp/python/2.7.5/python-2.7.5.msi).
* git
* pip (https://pypi.python.org/pypi/pip )
* xcode (on a Mac OSX)
* virtualenv (https://pypi.python.org/pypi/virtualenv)

With all the above installed, you can do the following to install and work with the script locally:

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


