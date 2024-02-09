import os
import PySimpleGUI as sg
from stashlib.logger import logger as log
from stashlib.stash_database import StashDatabase
from stashlib.stash_interface import StashInterface
from mapper import generate_mapping_from_export_zip, generate_mapping_from_directory, generate_mapping_from_export_dir, process_mapping

WINDOW_TITLE = 'Stash Metadata Mapper'
WINDOW_THEME = 'SystemDefaultForReal'
DEFAULT_MAPPING_FILENAME = "mapping.yaml"

def generate_gui():
    sg.theme(WINDOW_THEME)

    input_layout = [
        [sg.T('Input one of the following:')],
        [sg.Text('Directory', size=(12, 1)), sg.Input(), sg.FolderBrowse()],
        [sg.Text('Stash export file', size=(12, 1)), sg.Input(), sg.FileBrowse()],
    ]
    options_layout = [
        [sg.Text('Output filename', size=(12, 1)), sg.Input(default_text=DEFAULT_MAPPING_FILENAME)],
        [sg.Checkbox('Parse Filenames', key='parse_filenames')],
        [sg.Text('Filename Pattern', size=(12, 1)), sg.Input(key='filename_pattern')],
        [sg.Checkbox('Performer Only', key='performer_only', default=False)],
    ]
    layout = [[sg.Text("Generate mapping")],
            [sg.Frame('Mapping Source', input_layout)],
            [sg.Frame('Options', options_layout)],
            [sg.Submit(button_text='Run', key='simple_map_directory_scene_files'), sg.Cancel()],
            ]

    window = sg.Window(WINDOW_TITLE, layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'Cancel':
            window.close()
            break

        dirpath = values[0]
        exportfile = values[1]
        outfilename = values[2] or DEFAULT_MAPPING_FILENAME
        parse_filenames = values['parse_filenames']
        filename_pattern = values['filename_pattern'] or None
        performer_only = values['performer_only']
        log.LogDebug(f"parse_filenames {parse_filenames} filename_pattern {filename_pattern} performer_only {performer_only}")

        if not dirpath and not exportfile:
            log.LogError(f'no directory or stash export file entered')
            continue
        if dirpath and not os.path.isdir(dirpath):
            log.LogError(f'invalid directory: {dirpath}')
            continue
        if exportfile and not os.path.isfile(exportfile):
            log.LogError(f'invalid stash export file: {exportfile}')
            continue

        try:
            ## Create and process mapping of scenes in a site directory
            outfile = os.path.join(dirpath, outfilename)
            if dirpath:
                generate_mapping_from_directory(dirpath, outfile, performer_only, parse_filenames, filename_pattern=filename_pattern)
            elif exportfile and exportfile.endswith(".zip"):
                generate_mapping_from_export_zip(exportfile, outfile, performer_only, parse_filenames, filename_pattern=filename_pattern)
            elif exportfile and os.path.isdir(exportfile):
                generate_mapping_from_export_dir(exportfile, outfile, performer_only, parse_filenames, filename_pattern=filename_pattern)
            log.LogInfo(f"generated mapping {outfile}")
            break

        except Exception as e:
            log.LogError(str(e))

def process_gui(client: StashInterface, db: StashDatabase):
    sg.theme(WINDOW_THEME)

    layout = [[sg.Text("Process mapping")],
            [sg.Text('Mapping file', size=(12, 1)), sg.Input(), sg.FileBrowse()],
            [sg.Checkbox('URL From Name', key='url_from_name')],
            [sg.Checkbox('Create Performers', key='create_performers', default=True)],
            [sg.Checkbox('Update Mapping File', key='update_mapfile', default=True)],
            [sg.Checkbox('Update Stash', key='update_stash')],
            [sg.Submit(button_text='Run', key='simple_map_directory_scene_files'), sg.Cancel()],
            ]

    window = sg.Window(WINDOW_TITLE, layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'Cancel':
            window.close()
            break

        mapfile = values[0]
        url_from_name = values['url_from_name']
        create_performers = values['create_performers']
        update_mapfile = values['update_mapfile']
        update_stash = values['update_stash']
        log.LogDebug(f"url_from_name {url_from_name} create_performers {create_performers} update_mapfile {update_mapfile} update_stash {update_stash}")

        if not mapfile:
            log.LogError(f'no mapping file entered')
            continue
        if not os.path.isfile(mapfile):
            if os.path.isdir(mapfile):
                mapfile = os.path.join(mapfile, 'mapping.yaml')
                if not os.path.isfile(mapfile):
                    log.LogError(f'invalid file: {mapfile}')
                    continue
            else:
                log.LogError(f'invalid file: {mapfile}')
                continue

        try:
            ## Create and process mapping of scenes in a site directory
            process_mapping(client, db, mapfile, mapfile, url_from_name=url_from_name, create_performers=create_performers, update_mapfile=update_mapfile, update_stash=update_stash)
            log.LogInfo(f"processed mapping {mapfile}")
            break

        except Exception as e:
            log.LogError(str(e))
