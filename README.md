# STATegra EMS tool for GALAXY

Use this tool to automatically annotate your current history in a STATegra EMS instance.
The tool generates the *file provenance* for each selected file based on the current history and sends it to STATegra EMS, which will create a new Analysis instance associated to the selected Experiment.
This Analysis instance will describe the complete process followed to generate the selected files.
In addition, files can be stored in the corresponding Experiment data directory.

At the end of this document you can find some screenshots for this tool.

### How to install
1. Copy the whole directory at the Galaxy tools directory
```bash
cp -r tmp_dir/stategraems_push /usr/local/galaxy/tools/stategraems_push
```

2. Register the new tool in Galaxy. Add a new entry at the tool_conf.xml file in the desired section.  
```bash
vi /usr/local/galaxy/config/tool_conf.xml
```  
```xml
<?xml version='1.0' encoding='utf-8'?>
<toolbox monitor="true">
    <section id="getext" name="Get Data">
       [...]
    <section id="send" name="Send Data">
       <tool file="genomespace/genomespace_exporter.xml" />
       <tool file="stategraems_push/stategraems_push.xml" />
       [...]
```

3. Restart Galaxy

### How to use
TODO

### Some screenshots
*The tool in Galaxy*
TODO
