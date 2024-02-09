import argparse
import config
import os
import sys
from stashlib.logger import logger as log, LogLevel
from stashlib.stash_database import StashDatabase
from stashlib.stash_interface import StashInterface
from mapper import generate_mapping_from_directory, generate_mapping_from_export_zip, generate_mapping_from_export_dir, process_mapping

def dir_path(path):
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not a valid path")

def file_path(path):
    if os.path.isfile(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"{path} is not a valid path")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate and process yaml mapping files.')
    parser.add_argument('-d', '--directory', type=dir_path, help='directory to generate a yaml mapping file from')
    parser.add_argument('-p', '--process', type=file_path, help='input yaml file')
    parser.add_argument('-o', '--output', type=str, help='output yaml file')
    parser.add_argument('--input_zip', type=file_path, help='stash export zip file of stash scenes to generate a yaml mapping file from')
    parser.add_argument('--input_dir', type=file_path, help='stash export directory of stash scenes to generate a yaml mapping file from')
    parser.add_argument('--db_path', type=file_path, help="path to stash database")
    parser.add_argument('--api_key', type=str, help="stash api key")
    parser.add_argument('--server_url', type=str, help="stash server url")
    parser.add_argument('--performer_only', type=str, help='simplified mapping of performers names and urls only')
    parser.add_argument('--parse_filenames', action='store_true', help='parse filename for metadata')
    parser.add_argument('--filename_pattern', type=str, help='regex pattern to use for filename parsing')
    parser.add_argument('--url_from_name', action='store_true', help='look up performer url from name')
    parser.add_argument('--create_performers', action='store_true', help='create missing performers')
    parser.add_argument('--update_stash', action='store_true', help='update stash scenes according to mapping')
    parser.add_argument('--no_update_mapfile', action='store_true', help="don't write changes to mapping file")
    parser.add_argument('--log_level', type=int, default=3, choices=range(1, 6), help="log levels: 1=trace, 2=debug, 3=info, 4=warn, 5=error")
    args = parser.parse_args()

    log.plugin = False
    log.log_level = LogLevel(args.log_level)

    if args.directory:
        mapfile = args.output
        if not mapfile:
            mapfile = os.path.join(args.directory, 'mapping.yaml')
        generate_mapping_from_directory(args.directory, mapfile, args.performer_only, args.parse_filenames, args.filename_pattern)

    if args.input_zip:
        mapfile = args.output
        if not mapfile:
            mapfile = os.path.join(os.path.dirname(args.input_zip), 'mapping.yaml')
        generate_mapping_from_export_zip(args.input_zip, mapfile, args.performer_only, args.parse_filenames, args.filename_pattern)

    if args.input_dir:
        mapfile = args.output
        if not mapfile:
            mapfile = os.path.join(os.path.dirname(args.input_dir), 'mapping.yaml')
        generate_mapping_from_export_dir(args.input_dir, mapfile, args.performer_only, args.parse_filenames, args.filename_pattern)

    if args.process:
        db_path = args.db_path or config.db_path
        api_key = args.api_key or config.api_key
        server_url = args.server_url or config.server_url

        if not db_path:
            log.LogError("missing stash database path")
            sys.exit(1)
        if not server_url:
            log.LogError("missing stash url")
            sys.exit(1)

        client = StashInterface(None, api_key=api_key, server_url=server_url)

        try:
            db = StashDatabase(db_path)
        except Exception as e:
            log.LogError(str(e))
            sys.exit(0)

        outfile = args.output or args.process
        update_mapfile = not args.no_update_mapfile
        process_mapping(client, db, args.process, outfile, url_from_name=args.url_from_name, create_performers=args.create_performers, update_mapfile=update_mapfile, update_stash=args.update_stash)

        db.close()