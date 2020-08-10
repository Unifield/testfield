import utils
import sys

if __name__ == '__main__':
    hw_id = sys.argv[1]
    print("Setting hw_id to: ", hw_id)

    sync_db = utils.prefix_db_name('SYNC_SERVER')
    connection = utils.XMLRPCConnection(sync_db)
    ent_obj = connection.get('sync.server.entity')
    ids = ent_obj.search([])
    if len(ids) == 0:
        raise RuntimeError("Could not find entity to edit.")
    ent_obj.write(ids, {'hardware_id': hw_id})
