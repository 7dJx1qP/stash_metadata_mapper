import json
import os
import re
import zipfile
from stashlib.common import load_yaml, save_yaml, get_timestamp
from stashlib.logger import logger as log
from stashlib.stash_database import StashDatabase
from stashlib.scene_filename_parser import parse_filename
from stashlib.stash_interface import StashInterface

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
    log.LogDebug(f"scraped performer: {url} {name}")
    if scraped_data:
        if scraped_data["images"]:
            scraped_data["image"] = scraped_data["images"][0]
        for k in list(scraped_data.keys()):
            if k not in performer_fields:
                del scraped_data[k]
        scraped_data["gender"] = scraped_data["gender"].upper()
        if name:
            scraped_data["name"] = name
        if scraped_data['birthdate'] and not re.match(r'\d\d\d\d\-\d\d\-\d\d', scraped_data['birthdate']):
            del scraped_data['birthdate']
        if scraped_data['death_date'] and not re.match(r'\d\d\d\d\-\d\d\-\d\d', scraped_data['death_date']):
            del scraped_data['death_date']
        del scraped_data['aliases']
        del scraped_data['height']
    elif name:
        scraped_data = {
            "name": name,
            "url": url
        }
    else:
        log.LogError(f"no scrape data: {url} and no name")
        return None, None
    log.LogDebug(f"creating performer: {url} {name}")
    performer_id = client.createPerformer(scraped_data)
    log.LogInfo(f"created performer id {performer_id}")
    return performer_id, scraped_data

def generate_mapping_from_export_dir(exportdir, outfile, performer_only, parse_filenames, filename_pattern=None):
    try:
        filepaths = []
        scenesdir = os.path.join(exportdir, 'scenes')
        for file in os.listdir(scenesdir):
            scenejsonfile = os.path.join(scenesdir, file)
            mapping = json.load(open(scenejsonfile, encoding='utf-8'))
            filepaths.append(mapping['files'][0])
    except:
        raise Exception(f"error processing {exportdir}")
    generate_mapping(filepaths, outfile, performer_only, parse_filenames, filename_pattern)

def generate_mapping_from_export_zip(exportfile, outfile, performer_only, parse_filenames, filename_pattern=None):
    try:
        filepaths = []
        archive = zipfile.ZipFile(exportfile, 'r')
        for name in archive.namelist():
            if name.startswith('scenes/'):
                mapping = json.loads(archive.read(name))
                filepaths.append(mapping['files'][0])
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
                        'disambiguation': '',
                        'url': ''
                    })

        if not mapping_performers:
            mapping_performers.append({
                'name': '',
                'disambiguation': '',
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

def process_mapping(client: StashInterface, db: StashDatabase, mapfile, outfile, url_from_name=False, create_performers=True, update_mapfile=True, update_stash=False):
    mapping = load_yaml(mapfile)

    for filepath, mapdata in mapping.items():
        performer_only = isinstance(mapdata, list)

        if performer_only:
            performers = mapdata
        else:
            performers = mapdata['performers']

        scenes = db.get_scenes_from_filepath(filepath)
        for scene in scenes:
            if not performer_only and update_stash:
                if mapdata['title']:
                    db.scenes.update_title_by_id(scene.id, mapdata['title'], False)
                if mapdata['date']:
                    db.scenes.update_date_by_id(scene.id, mapdata['date'], False)
                if 'details' in mapdata and mapdata['details']:
                    db.scenes.update_details_by_id(scene.id, mapdata['details'], False)
                if 'studio' in mapdata and mapdata['studio']:
                    studio = db.studios.selectone_name(mapdata['studio'])
                    if studio:
                        db.scenes.update_studio_id_by_id(scene.id, studio.id, False)
                db.commit()
                if 'tags' in mapdata and mapdata['tags']:
                    for tag_name in mapdata['tags']:
                        tag = db.tags.selectone_name(tag_name)
                        if not tag:
                            db.tags.insert(tag_name, get_timestamp(), get_timestamp(), commit=True)
                            tag = db.tags.selectone_name(tag_name)
                        if tag:
                            db.add_tag_to_scene(scene, tag, commit=True)

            for actor in performers:
                name = actor['name']
                url = actor['url']
                performer = None
                performer_id = None

                # if only name and no url, try to find url from name
                if name and not url:
                    if url_from_name:
                        performer = db.query_performer_name(name)
                        if performer:
                            actor['url'] = performer.url
                # if only url and no name, try to find name from url
                elif url:
                    performer = db.performers.selectone_url(url)
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
                        performer_id = performer.id
                        actor['name'] = performer.name

                if scene and performer_id and update_stash:
                    performer = db.performers.selectone_id(performer_id)
                    if performer:
                        db.add_performers_to_scene(scene, [performer])

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
                'disambiguation': '',
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