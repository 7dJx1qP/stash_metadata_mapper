# Stash Metadata Mapper v1.1

A text-file based method of updating stash scene metadata.

Stash scene metadata import using YAML files.

Generate YAML files that associate scene files with metadata and then use them to update your stash.

## Overview

Suppose you had a directory with two files:
```
C:\Videos\Jane Doe - My First Scene (2021.10.11).mp4
C:\Videos\Jill, Jack - Another Scene (2021.11.08).mp4
```

The contents of a blank mapping file generated from this directory looks like:
```yaml
C:\Videos\Jane Doe - My First Scene (2021.10.11).mp4:
  performers:
  - name: ''
    url: ''
  date: ''
  title: ''
  url: ''
C:\Videos\Jill, Jack - Another Scene (2021.11.08).mp4:
  performers:
  - name: ''
    url: ''
  date: ''
  title: ''
  url: ''
```

Once you fill in the mapping file with the metadata you want, use it to update your stash scenes by running the [process mapping task](#process-mapping-task) with the update stash option, or running from the [command line](#command-line-arguments) with the update stash option. See the [walkthrough section](#walkthrough) below for details.

* All the fields are optional (`name`, `url`, `date`, `title`). You can leave them empty and they will just be ignored when the mapping file is used to update stash.

### Filename parsing

A mapping file can be generated with metadata already filled in by parsing filenames. A mapping file generated with filename parsing enabled looks like:

```yaml
C:\Videos\Jane Doe - My First Scene (2021.10.11).mp4:
  performers:
  - name: Jane Doe
    url: ''
  date: '2021-10-11'
  title: My First Scene
  url: ''
C:\Videos\Jill, Jack - Another Scene (2021.11.08).mp4:
  performers:
  - name: Jill
    url: ''
  - name: Jack
    url: ''
  date: '2021-11-08'
  title: Another Scene
  url: ''
```

### Performers

#### Adding performers to the mapping

You can also add performers to the mapping, just add more name, url entries. *Note: Correct indentation is important.*
```
  - name:
    url:
  - name:
    url:
```

#### Performer URLs from names

You can fill in the performer urls yourself, or the mapping process can automatically fill in urls from names if the names exist in stash.

#### Performer creation

The mapping process can create new performers by scraping urls if there's a supported stash scraper for them. If there's no scraper, a new performer with just name and url is created.

#### Simplified performer only mapping file

If you're only interested in mapping performers to files, there is a simplified format:
```yaml
C:\Videos\Jane Doe - My First Scene (2021.10.11).mp4:
- name: Jane Doe
  url: ''
C:\Videos\Jill, Jack - Another Scene (2021.11.08).mp4:
- name: Jill
  url: ''
- name: Jack
  url: ''
```

# Requirements

Python 3.6+

# Installation

The mapper can be used as a plugin which launches a GUI window or it can be run as a command line script.

I've tested the plugin on Windows. Linux and Mac compatability is unknown. If you're using stash on Docker or the plugin doesn't work, just use the command line script.

## Plugin

Place the `stash_metadata_mapper` folder in your stash `plugins` folder

Run `pip install -r requirements.txt` in the `stash_metadata_mapper` folder

## Script

Fill in `config.py` with your stash api key and stash url

Run `pip install -r requirements.txt` in the `stash_metadata_mapper` folder

# Usage

## Plugin

Run the tasks and a GUI window will appear. The options in the GUI correspond to the script command line arguments described below

### Generate Mapping Task

![image](https://user-images.githubusercontent.com/38586902/141648536-963a1f30-d8b2-4f12-a14c-f7424bd750dc.png)

### Process Mapping Task

![image](https://user-images.githubusercontent.com/38586902/141648568-c2bd81fe-1797-43b8-937a-4944d2956ca4.png)


## Script

The command line script is `cli.py`

### Command Line Arguments

* `-d`, `--directory` `<path to folder>` Generate a YAML mapping file from files in given directory
* `-p`, `--process` `<path to file>` Process the given YAMl mapping file
* `-o`, `--output` `<path to file>` YAML file output destination
* `--input_zip` `<path to stash export zip>` Generate a YAML mapping file from a stash export zip
* `--input_json` `<path to stash export mappings.json>` Generate a YAML mapping file from a stash export mappings.json
* `--api_key` Stash API key
* `--server_url` Stash server URL
* `--performer_only` Generate a performer only mapping file. Useful if you are only interested in updating scenes with performers and no other scene metadata
* `--parse_filenames` Parse filenames for metadata according to a pattern. If your filenames follow a pattern, i.e. `{performer} - {title} ({date}).{ext}`, parsing filenames can prefill the mapping
* `--filename_pattern` Regex pattern describing how to parse filenames
* `--url_from_name` Populate performer urls in mapping by looking up names in stash for existing performers
* `--create_performers` Create missing performers in stash by scraping performer url
* `--update_stash` Update stash scene metadata according to mapping
* `--no_update_mapfile` Don't modify the input mapping file. Processing a mapping file may modify it, i.e. the `url_from_name` option fills in the mapping performer urls based on performer names. Use no_update_mapfile to prevent the mapping file from being updated.

### Walkthrough

*Note: you may need to replace py with python or python3 when you run commands, depending on your setup*

1. Generate a mapping file:

    * From a directory of files

      `py cli.py --directory C:\Videos --parse_filenames --filename_pattern pattern`

      `mapping.yaml` will be created in `C:\Videos`

    * From a stash export zip

      `py cli.py --directory C:\export20211112-185658.zip --parse_filenames --filename_pattern pattern`

      `mapping.yaml` will be created in `C:`

    * From a stash export mappings.json

      `py cli.py --directory C:\export20211112-185658\mappings.json --parse_filenames --filename_pattern pattern`

      `mapping.yaml` will be created in `C:\export20211112-185658`

2. Fill in performer urls in mapping from performer names in mapping:

    `py cli.py --process C:\Videos\mapping.yaml --url_from_name`

3. Create missing performers from performer urls:

    `py cli.py --process C:\Videos\mapping.yaml --create_performers`

4. Review `mapping.yaml` and fill in an missing data or make corrections. You can repeat steps 2 and 3 as needed. Both options can be used at the same time as well:

    `py cli.py --process C:\Videos\mapping.yaml --url_from_name --create_performers`

5. Update stash scenes according to mapping:

    `py cli.py --process C:\Videos\mapping.yaml --update_stash`

    * Note: Up to this point, the files in the mapping don't need to have been scanned into stash yet. But you will need to scan your files into stash for `update_stash` to work.

## Additional Fields

* `details` aren't included when generating a full mapping, but you can add them in and they will be processed, i.e.
```yaml
C:\Videos\Jane Doe - My First Scene (2021.10.11).mp4:
  performers:
  - name: Jane Doe
    url: ''
  date: '2021-10-11'
  title: My First Scene
  url: ''
  details: This is a description of the scene
```

## Parse Patterns

The `filename_pattern` option allows you to pass a regex pattern describing how to parse filenames for metadata.

The parser checks for the following named capture groups: `studio`, `title`, `date`, `performers`

Parsing support is currently limited as it's been developed with my own particular file-naming conventions in mind. Feel free to open an issue describing the filename parsing support you need and I'll try to implement it.

### Examples

`--filename_pattern "^(?P<date>\d{4}\-\d\d\-\d{2}) (?P<title>.*?)$"` would parse filenames in the form `{YYYY-MM-DD} {title}`

### Default capture groups

If no `filename_pattern` is given, these are how the capture groups are defined:

`studio`: `\[(?P<studio>[a-zA-Z0-9]+)\]` alphanumeric, no spaces, surrounded by brackets
`title`: `(?P<title>.*?)` match any string of characters, non-greedy
`performers`: `(?P<performers>[a-zA-Z0-9 ,']+)` alphanumeric + spaces, comma-separated
`date`: `\((?P<date>\d{2,4}\.\d\d\.\d{2,4})\)` some variation of (XX.XX.XXXX), (XXXX.XX.XX) or (XX.XX.XX). parser tries to convert to YYYY-MM-DD if unambiguous, otherwise date is not used

### Default patterns

If no `filename_pattern` is given, then the parser will try to match against a few default patterns constructed from the named capture groups defined above

```
{studio} {performers} - {title} {date}
{studio} {performers} - {title}
{studio} {performers} {date}
{studio} {performers}
{performers} - {title} {date}
{performers} - {title}
{title} {date}
```
