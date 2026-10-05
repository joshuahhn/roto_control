"""COMP visual ownership for acknowledged parameter mappings; no target writes."""
TAG = 'roto_mapped'
COLOR = (.20, .55, .70)
KEY = '_roto_mapping_visual'
TRACKED = '_roto_mapping_visual_ids'


def _same_color(a, b):
    return all(abs(x-y)<1e-6 for x,y in zip(a,b))


def _release(node, record):
    if record['tag_added']:
        node.tags.discard(TAG)
    if _same_color(node.color, record['applied_color']):
        node.color = tuple(record['original_color'])
    node.store(KEY, None)


def update(controller, states, resolve=None):
    if resolve is None:
        resolve = op
    owner_id = str(controller.id)
    desired = {}
    for state in states:
        if state['valid'] and state['mapped'] and state['connected'] and state['plugin'] and state['binding_type'] in ('parameter','value') and state['comp']:
            node = resolve(state['comp'])
            if node is not None and node.valid and node.isCOMP:
                desired[node.id] = node
    previous = controller.fetch(TRACKED, [])
    for node_id in set(previous) | set(desired):
        node = desired.get(node_id) or resolve(node_id)
        if node is None or not node.valid:
            continue
        record = node.fetch(KEY, None)
        if record:
            owners = {}
            for id, path in record['owners'].items():
                owner = resolve(int(id))
                if owner is not None and owner.valid and (owner.path == path or id == owner_id):
                    status = owner.op('base_state')
                    if status is not None and status.par.Connected.eval() and status.par.Plugin.eval():
                        owners[id] = owner.path
            if node_id not in desired:
                owners.pop(owner_id, None)
            record = dict(record, owners=owners)
            if not owners:
                _release(node,record)
                record = None
        if node_id in desired:
            if record is None:
                record = dict(original_color=tuple(node.color), tag_added=TAG not in node.tags, owners={})
                node.tags.add(TAG)
                node.color = COLOR
                record['applied_color'] = tuple(node.color)
            record['owners'][owner_id] = controller.path
            node.store(KEY,record)
        elif record is not None:
            node.store(KEY,record)
    controller.store(TRACKED, list(desired))
