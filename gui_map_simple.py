import os
import PySimpleGUI as sg
from stash_interface import StashInterface
from mapper import map_directory_scene_files
from log import log

WINDOW_TITLE = 'Stash Manager'
WINDOW_THEME = 'SystemDefaultForReal'

def gui_map_simple(client: StashInterface):
    sg.theme(WINDOW_THEME)

    layout = [[sg.Text("Create and process simple mapping of a directory")],
            [sg.Text('Folder', size=(12, 1)), sg.Input(), sg.FolderBrowse()],
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
        if not dirpath:
            log.LogError(f'no directory entered')
            continue
        if not os.path.isdir(dirpath):
            log.LogError(f'invalid directory: {dirpath}')
            continue

        try:
            ## Create and process mapping of scenes in a site directory
            log.LogInfo(f"starting {dirpath}")
            map_directory_scene_files(client, dirpath, performer_only=True, parse_filenames=True, url_from_name=True)
            log.LogInfo(f"mapped {dirpath}")
            break

        except Exception as e:
            log.LogError(e)
