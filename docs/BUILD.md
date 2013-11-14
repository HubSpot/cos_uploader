Here this command I - Patrick Fitzsimmons - use to build the executable distribution:

```bash
pyinstaller --onefile sync_to_cos.py --hidden-import="markdown.extensions.headerid" --hidden-import=ordereddict --hidden-import="markdown.extensions.codehilite" --hidden-import="markdown.extensions.fenced_code" --hidden-import="markdown.extensions.toc" --paths=/Users/pfitzsimmons/dev/virtualenvs/cos_syncer/lib/python2.7/site-packages:/Users/pfitzsimmons/dev/src/snakecharmer;mv /Users/pfitzsimmons/dev/src/cos_syncer/cos_syncer/dist/sync_to_cos /Users/pfitzsimmons/dev/src/designers_site

```