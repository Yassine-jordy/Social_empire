"""Legacy collection counts: upstream 880cde18 version.fix_collections/op.

Index zero is empty; 23 collections each contain a completion flag followed
by five item counters. Reject slot 6, which upstream op permits erroneously
despite its six-element rows.
"""


def add(save, args):
    if not isinstance(args, list) or len(args) != 2:
        raise ValueError('Invalid collectible arguments')
    collection_id, index = args
    if type(collection_id) is not int or not 1 <= collection_id <= 23:
        raise ValueError('Invalid collection ID')
    if type(index) is not int or not 1 <= index <= 5:
        raise ValueError('Invalid collectible index')
    private = save['privateState']
    collections = private.get('collections')
    if collections is None or collections == []:
        collections = [[]] + [[0] * 6 for _ in range(23)]
        private['collections'] = collections
    if not isinstance(collections, list) or len(collections) != 24 or collections[0] != []:
        raise ValueError('Invalid collections state')
    row = collections[collection_id]
    if not isinstance(row, list) or len(row) != 6 or any(type(n) is not int or n < 0 for n in row):
        raise ValueError('Invalid collectible counts')
    row[index] += 1
