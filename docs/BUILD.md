Building the cos_uploader requires pyinstaller ( http://www.pyinstaller.org/ )

```
pip install pyinstaller
```

Once you have installed pyinstaller, you can then build a single executable:

On OSX:
```bash
cd cos_uploader
./build_binary.sh
```

On Windows:
```bash
cd cos_uploader
./build_exe.bat
```

The executable ends up in the folder "dist" You should then test out using this executable with a COS site and make sure it actually works. 

Once you have verified the executable works, create a new release in github. Attach the OSX and Windows binaries.

Then login into portal 327485, go to Content Settings->Url Mappings and update the /cos-uploader... mappings to point to the new release.

