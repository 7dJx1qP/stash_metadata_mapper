import os
import PySimpleGUI as sg
from stash_interface import StashInterface
from mapper import map_directory_scene_files
from log import log

WINDOW_TITLE = 'Stash Manager'
WINDOW_THEME = 'SystemDefaultForReal'

def gui_map_directory(client: StashInterface):
    sg.theme(WINDOW_THEME)

    layout = [[sg.Text("Create and process mapping of a directory")],
            [sg.Text('Folder', size=(12, 1)), sg.Input(), sg.FolderBrowse()],
            [sg.Checkbox('Parse Filenames', key='parse_filenames')],
            [sg.Text('Filename Pattern', size=(12, 1)), sg.Input(key='filename_pattern')],
            [sg.Checkbox('URL From Name', key='url_from_name')],
            [sg.Checkbox('Create Performers', key='create_performers', default=True)],
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

        dirpath = values[0]
        parse_filenames = values['parse_filenames']
        filename_pattern = values['filename_pattern'] or None
        url_from_name = values['url_from_name']
        create_performers = values['create_performers']
        update_stash = values['update_stash']
        log.LogDebug(f"parse_filenames {parse_filenames} filename_pattern {filename_pattern} url_from_name {url_from_name} create_performers {create_performers} update_stash {update_stash}")

        if not dirpath:
            log.LogError(f'no directory entered')
            continue
        if not os.path.isdir(dirpath):
            log.LogError(f'invalid directory: {dirpath}')
            continue

        try:
            ## Create and process mapping of scenes in a site directory
            map_directory_scene_files(client, dirpath, performer_only=False, parse_filenames=parse_filenames, filename_pattern=filename_pattern, url_from_name=url_from_name, create_performers=create_performers, update_stash=update_stash)
            log.LogInfo(f"mapped {dirpath}")
            break

        except Exception as e:
            log.LogError(e)
