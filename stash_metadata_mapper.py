import sys
import json
from gui_map_simple import gui_map_simple
from gui_map_directory import gui_map_directory
from log import log
from stash_interface import StashInterface

def read_json_input():
    json_input = sys.stdin.read()
    return json.loads(json_input)
    
if __name__ == "__main__":
    json_input = read_json_input()
    mode_arg = json_input['args']['mode']
    client = StashInterface(json_input["server_connection"])

    try:
        log.LogInfo("mode: {}".format(mode_arg))

        if mode_arg == 'map_simple':
            gui_map_simple(client)

        elif mode_arg == 'map_directory':
            gui_map_directory(client)

    except Exception as e:
        log.LogError(str(e))

    log.LogInfo('done')
    output = {}
    output["output"] = "ok"
    out = json.dumps(output)
    print(out + "\n")