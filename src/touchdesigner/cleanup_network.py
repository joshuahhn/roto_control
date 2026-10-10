"""Plan and verify controller-only presentation changes using actual node sizes."""

GROUPS = {
    '': [
        ('Host', ['RotoPythonExt', 'protocol', 'parameter_callbacks', 'lifecycle_callbacks', 'midi_process'], 2),
        ('Binding', ['binding', 'snapshots', 'target_callbacks', 'registration', 'setup', 'layouts', 'layout_migration'], 2),
        ('Collection', ['base_targets', 'collection_protocol', 'controls'], 2),
        ('Free Learn', ['free_learn', 'learn_parameters'], 2),
        ('State', ['base_state'], 1),
        ('Inspector', ['inspector'], 1),
        ('Guide', ['readme_md', 'docs'], 2),
        ('Focus', ['text_comp_follow'], 1),
        ('Value output', ['parameter_values', 'null_values', 'out_values'], 3),
        ('Control output', ['select_controls', 'null_controls', 'out_controls'], 3),
    ],
    'base_targets': [
        ('Database', ['targets', 'state'], 2),
        ('Knob watchers', [f'watch_knob{i}' for i in range(1, 9)], 4),
        ('Button watchers', [f'watch_button{i}' for i in range(1, 9)], 4),
        ('Events', ['rx_events', 'mapping_marks'], 2),
        ('Output', ['controls_values', 'null_controls', 'out_controls'], 3),
    ],
    'inspector': [
        ('Publication', ['targets', 'database', 'context_state', 'inspector_data', 'owned_runtime'], 2),
        ('Shared model', ['inspector_model'], 1),
        ('Fold + editor', ['inspector_below'], 1),
        ('Popup presentation', ['inspector_popup'], 1),
    ],
    'docs': [
        ('Overview', ['overview_md', 'functions_md'], 2),
        ('Functions', ['fn_binding_md', 'fn_controls_md', 'fn_inspector_md', 'fn_lifecycle_md', 'fn_portability_md', 'fn_layouts_md', 'fn_actions_md', 'fn_snapshots_md'], 3),
    ],
}


def plan(comp):
    """Return batched positions and annotations without modifying the network."""
    result = []
    for relative, definitions in GROUPS.items():
        parent = comp if not relative else comp.op(relative)
        if parent is None:
            continue
        positions, boxes = {}, []
        # Three columns of functional groups; rows use measured maximum height.
        layouts = []
        for title, names, columns in definitions:
            nodes = [parent.op(name) for name in names if parent.op(name) is not None]
            if not nodes:
                continue
            column_width = max(node.nodeWidth for node in nodes) + 45
            row_height = max(node.nodeHeight for node in nodes) + 45
            local = {}
            for index, node in enumerate(nodes):
                x = 25 + (index % columns) * column_width
                y = -(index // columns) * row_height - node.nodeHeight
                local[node.name] = [x, y]
            width = max(local[n.name][0] + n.nodeWidth for n in nodes) + 25
            bottom = min(local[n.name][1] for n in nodes) - 25
            layouts.append((title, local, width, 60 - bottom, nodes))
        # Uniform widths per column and heights per row, with 20px box gaps.
        widths = [max((item[2] for i, item in enumerate(layouts) if i % 3 == col), default=0) for col in range(3)]
        x_starts = [0, widths[0] + 20, widths[0] + widths[1] + 40]
        top = 150
        for start in range(0, len(layouts), 3):
            row = layouts[start:start + 3]
            height = max(item[3] for item in row)
            for column, (title, local, width, own_height, nodes) in enumerate(row):
                x = x_starts[column]
                for name, (local_x, local_y) in local.items():
                    positions[name] = [x + local_x, top - 60 + local_y]
                boxes.append({'title': title, 'names': list(local), 'x': x, 'y': top - height,
                              'w': widths[column], 'h': height})
            top -= height + 20
        leftovers = [n.name for n in parent.children if n.OPType != 'annotateCOMP' and n.name not in positions]
        if leftovers:
            raise ValueError(f'Unclassified operators at {parent.path}: {leftovers}')
        result.append({'path': parent.path, 'positions': positions, 'boxes': boxes})
    return result


def verify(comp, plans):
    checked = 0
    for entry in plans:
        parent = op(entry['path'])
        nodes = [parent.op(name) for name in entry['positions']]
        for box in entry['boxes']:
            for name in box['names']:
                node = parent.op(name)
                assert node.nodeX >= box['x'] + 25, node.path
                assert node.nodeY >= box['y'] + 25, node.path
                assert node.nodeX + node.nodeWidth <= box['x'] + box['w'] - 25, node.path
                assert node.nodeY + node.nodeHeight <= box['y'] + box['h'] - 60, node.path
                checked += 1
        for i, a in enumerate(entry['boxes']):
            for b in entry['boxes'][i + 1:]:
                assert (a['x'] + a['w'] + 20 <= b['x'] or b['x'] + b['w'] + 20 <= a['x'] or
                        a['y'] + a['h'] + 20 <= b['y'] or b['y'] + b['h'] + 20 <= a['y'])
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                assert (a.nodeX + a.nodeWidth <= b.nodeX or b.nodeX + b.nodeWidth <= a.nodeX or
                        a.nodeY + a.nodeHeight <= b.nodeY or b.nodeY + b.nodeHeight <= a.nodeY), (a.path, b.path)
        for node in nodes:
            for source in node.inputs:
                assert source.nodeX < node.nodeX, (source.path, node.path, 'backward wire')
    return {'networks': len(plans), 'groups': sum(len(p['boxes']) for p in plans), 'operators': checked,
            'containment': True, 'overlaps': False, 'backward_wires': False}


def apply(comp, obsolete_annotations=()):
    """Apply the measured recipe to this controller only; leave panel geometry.

    Remove only our tagged groups or exact
    obsolete annotation paths supplied by the caller. Other user notes survive.
    Every functional node must remain
    explicitly classified by plan(). Unclassified user nodes stop cleanup.
    """
    plans = plan(comp)
    for entry in plans:
        parent = comp if entry['path'] == comp.path else comp.op(entry['path'])
        for node in tuple(parent.children):
            if node.OPType == 'annotateCOMP' and (
                    node.fetch('roto_network_group',False) or
                    node.path in obsolete_annotations):
                node.destroy()
        for name, (x, y) in entry['positions'].items():
            node = parent.op(name)
            node.nodeX, node.nodeY = x, y
        for index, box in enumerate(entry['boxes']):
            node = parent.create(annotateCOMP, 'annotate_roto_group'+str(index))
            node.store('roto_network_group',True)
            node.par.Mode = 'networkbox'
            node.par.Titletext = box['title']
            node.nodeX, node.nodeY = box['x'], box['y']
            node.nodeWidth, node.nodeHeight = box['w'], box['h']
    return verify(comp, plans)
