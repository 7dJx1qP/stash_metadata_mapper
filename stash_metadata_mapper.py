import config
import sys
import json
from stashlib.logger import logger as log
from stashlib.stash_database import StashDatabase
from stashlib.stash_interface import StashInterface
from mapper_gui import generate_gui, process_gui

def read_json_input():
    json_input = sys.stdin.read()
    return json.loads(json_input)
    
if __name__ == "__main__":
    json_input = read_json_input()
    mode_arg = json_input['args']['mode']
    client = StashInterface(json_input["server_connection"])

    try:
        db = StashDatabase(config.db_path)
    except Exception as e:
        log.LogError(str(e))
        sys.exit(0)

    try:
        log.LogInfo("mode: {}".format(mode_arg))

        if mode_arg == 'generate':
            generate_gui()

        elif mode_arg == 'process':
            process_gui(client, db)

    except Exception as e:
        log.LogError(str(e))

    db.close()

    log.LogInfo('done')
    output = {}
    output["output"] = "ok"
    out = json.dumps(output)
    print(out + "\n")