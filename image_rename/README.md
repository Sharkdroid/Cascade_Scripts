# Image Renaming Script

### Description
Rename images in a given site.<br>
**program flow:**<br>
rename the displayName (if applicable) &rarr; rename with move operation & unpublish &rarr; republish image asset &rarr; republish all related assets

### Prequisites
Make sure you follow the installation process [here](https://github.com/Sharkdroid/Cascade-Scripts) before continuing

### CSV format
```csv
destination_path,newname
xxxxxxxx/xxxxxxx/xxxxxx/xxxxxxxxxxxx.png,xxxxxxxxx
xxxxxxx/xxxxx/xxxxxx/xxxxxxxxxxxxxx.png,xxxxxxxxx
xxxxxxx/xxxxx/xxxxxx/xxxxxxxxxxxxxx.png,xxxxxxx
```

### Format
The CSV has to be in a specific format or else the program won't function properly. While viewing the csv file click `Align` at the bottom of the window, it should change to `Shrink` click it again this will remove any trailing whitespaces.

### Other notes
The parent asset needs to be publishable or else the program won't work correctly.

##### Related Scripts
|scripts| description |
|---------|----------|
|[sitemap](https://github.com/Sharkdroid/Cascade-Scripts/tree/sitemap)| creating sitemap out of csv files |
|[xml_edit](https://github.com/Sharkdroid/Cascade-Scripts/tree/xml_edit)| editing XML property |
