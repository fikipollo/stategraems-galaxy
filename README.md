# STATegra EMS tool for GALAXY

### What it does

Use this tool to automatically annotate your current history in your STATegra EMS instance.
The tool obtains the *file provenance* for each selected file based on the current history and sends it to the STATegra EMS, where a new Analysis instance is created associated to the selected Study.
This Analysis instance will describe the complete process followed to generate the selected files.
Additionally, the resulting files can be stored in the data directory for the selected study.

At the end of this document you can find some screenshots for this tool.

### How to use

1. Write a valid *URL* to your STATegra EMS host (e.g. http://bioinfo.cipf.es/stategraems)
2. Sign in your STATegra EMS and copy your *API code* (more info http://stategraems.readthedocs.io/en/latest/tutorials/api/)
3. Enter your API code in the form.
4. Type the a valid identifier for a *study* in the STATegra EMS (you must be a valid member of the study, e.g. "EXP00001").
5. Enter a name for the new analysis that will be created in the STATegra EMS (e.g. "My awesome RNA-seq analysis").
6. Choose all the datasets in the history that will be annotated as part as the new analysis.
7. Choose whether you want to send just the description of the datasets generation, or upload the metadata and the generated datasets.

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

### Some screenshots
*The tool in Galaxy*
TODO
