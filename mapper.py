import json
import os
from log import log
import re
import zipfile
from common import load_yaml, save_yaml
from scene_filename_parser import parse_filename
from stash_interface import StashInterface

"""Functions for creating mapping files, creating performers, and updating stash scenes
"""

skip_exts = ['.jpg', '.txt', '.json', '.yml', '.yaml']

performer_fields = ["name", "url", "gender", "birthdate", "ethnicity",
            "country", "eye_color", "height", "measurements", "fake_tits",
            "career_length", "tattoos", "piercings", "aliases", "twitter",
            "instagram", "favorite", "tag_ids", "image", "stash_ids",
            "rating", "details", "death_date", "hair_color", "weight"]

def create_performer_from_url(client: StashInterface, url, name=None):
    scraped_data = client.scrapePerformerURL(url)
    if scraped_data:
        if scraped_data["images"]:
            scraped_data["image"] = scraped_data["images"][0]
        for k in list(scraped_data.keys()):
            if k not in performer_fields:
                del scraped_data[k]
        scraped_data["gender"] = scraped_data["gender"].upper()
        if name:
            scraped_data["name"] = name
    elif name:
        scraped_data = {
            "name": name,
            "url": url
        }
    else:
        log.LogError(f"no scrape data: {url} and no name")
        return None, None
    performer_id = client.createPerformer(scraped_data)
    log.LogInfo(f"created performer id {performer_id}")
    return performer_id, scraped_data

def generate_mapping_from_export_json(jsonfile, outfile, performer_only, parse_filenames, filename_pattern=None):
    try:
        mapping = json.load(open(jsonfile, encoding='utf-8'))
        filepaths = [scene['path'] for scene in mapping['scenes']]
    except:
        raise Exception(f"error loading {jsonfile}")
    generate_mapping(filepaths, outfile, performer_only, parse_filenames, filename_pattern)

def generate_mapping_from_export_zip(exportfile, outfile, performer_only, parse_filenames, filename_pattern=None):
    try:
        archive = zipfile.ZipFile(exportfile, 'r')
        mapping = json.loads(archive.read('mappings.json'))
        filepaths = [scene['path'] for scene in mapping['scenes']]
    except:
        raise Exception("error reading mapping.json from export file")
    generate_mapping(filepaths, outfile, performer_only, parse_filenames, filename_pattern)

def generate_mapping_from_directory(dirpath, outfile, performer_only, parse_filenames, filename_pattern=None):
    filepaths = [os.path.join(dirpath, file) for file in os.listdir(dirpath)]
    generate_mapping(filepaths, outfile, performer_only, parse_filenames, filename_pattern)

def generate_mapping(filepaths, outfile, performer_only, parse_filenames, filename_pattern=None):
    mapping = load_yaml(outfile)
    for filepath in filepaths:
        if not os.path.isfile(filepath):
            continue
        filename, ext = os.path.splitext(os.path.basename(filepath))
        if ext in skip_exts:
            continue
        log.LogInfo(filepath)

        if not performer_only:
            mapping[filepath] = {
                'url': '',
                'date': '',
                'title': '',
            }
        mapping_performers = []

        if parse_filenames:

            parsed, studio, performers, title, date = parse_filename(os.path.splitext(os.path.basename(filepath))[0], filename_pattern)
            log.LogDebug(f"{parsed}, {studio}, {performers}, {title}, {date}")

            if parsed:
                if not performer_only:
                    if title:
                        mapping[filepath]['title'] = title
                    if date:
                        mapping[filepath]['date'] = date

                if performers:
                    for performer in performers:
                        mapping_performers.append({
                        'name': performer,
                        'url': ''
                    })

        if not mapping_performers:
            mapping_performers.append({
                'name': '',
                'url': ''
            })

        if performer_only:
            mapping[filepath] = mapping_performers
        else:
            mapping[filepath]['performers'] = mapping_performers
    
    save_yaml(outfile, mapping)

def get_scene_from_filepath(client: StashInterface, filepath):
    scenes = client.findScenesByPathRegex(re.escape(filepath))
    if scenes:
        return scenes[0]
    return None

def process_mapping(client: StashInterface, mapfile, outfile, url_from_name=False, create_performers=True, update_mapfile=True, update_stash=False):
    mapping = load_yaml(mapfile)

    for filepath, mapdata in mapping.items():
        performer_only = isinstance(mapdata, list)

        if performer_only:
            performers = mapdata
        else:
            performers = mapdata['performers']

        scene = get_scene_from_filepath(client, filepath)
        if scene and update_stash:
            scene_data = {
                "id": scene["id"],
            }
            if not performer_only:
                if mapdata['title']:
                    scene_data['title'] = mapdata['title']
                if mapdata['date']:
                    scene_data['date'] = mapdata['date']
                if mapdata['url']:
                    scene_data['url'] = mapdata['url']
                if 'details' in mapdata and mapdata['details']:
                    scene_data['details'] = mapdata['details']
                if len(scene_data.keys()) > 1:
                    client.updateScene(scene_data)

        for actor in performers:
            name = actor['name']
            url = actor['url']
            performer = None
            performer_id = None

            # if only name and no url, try to find url from name
            if name and not url:
                if url_from_name:
                    performer = client.findPerformerByName(name)
                    if performer:
                        actor['url'] = performer.get("url")
            # if only url and no name, try to find name from url
            elif url:
                performer = client.findPerformerByURL(url)
                # try to create performer if url not found
                if not performer:
                    if create_performers:
                        log.LogDebug(f'creating missing performer {url}')
                        performer_id, scraped_data = create_performer_from_url(client, url, name)
                        # get name from performer if create successful
                        if performer_id:
                            actor['name'] = scraped_data["name"]
                            log.LogInfo(f"created performer {actor['name']}")
                        else:
                            log.LogWarning(f'failed to create performer {url}')
                else:
                    performer_id = performer.get("id")
                    actor['name'] = performer.get("name")

            if scene and performer_id and update_stash:
                performer_ids = [x["id"] for x in scene["performers"]]
                if performer_id not in performer_ids:
                    performer_ids.append(performer_id)
                client.updateScene({
                    "id": scene["id"],
                    "performer_ids": performer_ids
                })

            log.LogDebug(f'\t{name} {url}')

    if update_mapfile:
        save_yaml(outfile, mapping)

def map_directory_scene_files(client: StashInterface, dirpath, performer_only=True, parse_filenames=False, filename_pattern=None, url_from_name=False, create_performers=True, update_mapfile=True, update_stash=False):
    """Generate a yaml file listing all scene files in a given directory
    Each scene file entry has pairs of performer names and urls
    The yaml file is processed and performers are created from urls and added to scenes.
    Maps performers, scene url, title, and date to file
    """

    mapfile = os.path.join(dirpath, 'mapping.yaml')

    if not os.path.isfile(mapfile):
        generate_mapping_from_directory(dirpath, mapfile, performer_only=performer_only, parse_filenames=parse_filenames, filename_pattern=filename_pattern)
    else:
        process_mapping(client, mapfile, mapfile, url_from_name=url_from_name, create_performers=create_performers, update_mapfile=update_mapfile, update_stash=update_stash)

def map_directory_performers(client: StashInterface, rootdir):
    """Create and processing mapping file for performer root directory
    Creates performer if name and url is given and performer does not exist
    Checks if url exists and stash name does not match mapping name
    """

    mapfile = os.path.join(rootdir, 'mapping.yaml')
    mapping = load_yaml(mapfile)

    for dirname in os.listdir(rootdir):
        dirpath = os.path.join(rootdir, dirname)
        if not os.path.isdir(dirpath):
            continue

        log.LogInfo(dirpath)

        if dirpath not in mapping:
            mapping[dirpath] = [{
                'name': dirname,
                'url': ''
            }]
        else:
            
            for actor in mapping[dirpath]:
                name = actor['name']
                url = actor['url']
                performer = None

                # if only name and no url, try to find url from name
                if name and not url:
                    performer = client.findPerformerByName(name)
                    if performer:
                        actor['url'] = performer.get("url")
                # if url and name, get performer if exists or create if not
                elif name and url:
                    performer = client.findPerformerByURL(url)
                    # try to create performer if url not found
                    if not performer:
                        log.LogDebug(f'creating missing performer {url}')
                        performer_id, scraped_data = create_performer_from_url(client, url, name)
                        # get name from performer if create successful
                        if performer_id:
                            log.LogInfo(f"created performer {actor['name']}")
                        else:
                            log.LogWarning(f'failed to create performer {url}')
                    elif performer.get("name") != actor['name']:
                        log.LogWarning(f"existing performer name mismatch {actor['name']} {performer.get('name')}")

                log.LogDebug(f'\t{name} {url}')

    save_yaml(mapfile, mapping)