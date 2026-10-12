"""Shared target resolution and result storage for the four native Popup probes.

No TD mutation happens here. Callers retain their separate geometry experiments.
"""
from pathlib import Path
import json
import tempfile


def prepare(scope, require_popup=True):
    """Require an explicit view; derive its model rather than guessing root OPs."""
    target = scope.get('view_path')
    if not target or not isinstance(target, str) or not target.startswith('/'):
        raise ValueError('Set view_path to the absolute Inspector view OP path')
    view = scope['op'](target)
    if view is None:
        raise ValueError(f'Inspector view not found: {target}')
    ui = view.ext.InspectorView
    model = ui._model
    popup = ui._popup
    if model is None or popup is None:
        raise ValueError('Inspector view must have an initialized model and Popup')
    if not ui._main.isOpen or (require_popup and not popup.isOpen):
        raise ValueError('Open the main Inspector and settle the Popup before this probe')
    controller = model.ownerComp.par.Controller.eval()
    if controller is None:
        raise ValueError('Inspector model must be attached to a controller')

    def write_result(filename, result):
        # Labels may be supplied by the caller; never let them escape output_dir.
        if Path(filename).name != filename or filename in ('', '.', '..'):
            raise ValueError('Result filename must be a single path component')
        output = scope.get('output_dir')
        directory = Path(output) if output is not None else Path(
            tempfile.mkdtemp(prefix='roto-popup-'))
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        path.write_text(json.dumps(result, indent=2) + '\n')
        print(f'Popup probe result: {path}')
        return path

    return dict(v=view, u=ui, p=popup, m=model.ownerComp, c=controller,
                controller=controller, write_result=write_result)
