"""Execute in TD, then build(explicit_parent, project_dir). No hardware auto-start."""

import os
from pathlib import Path


def build(parent_comp, source_dir):
    source = Path(source_dir).resolve()
    if parent_comp is None or not parent_comp.isCOMP:
        raise ValueError("Pass an explicit parent COMP")
    if parent_comp.op("roto_python") is not None:
        raise FileExistsError("roto_python already exists; update its synced source in place")
    # Validate source before constructing anything.
    code_dir = source / "code/py/roto_python"
    files = {name: (code_dir / f"{name}.py").read_text() for name in
             ("protocol", "RotoPythonExt", "parameter_callbacks", "lifecycle_callbacks")}
    docs_path = source / "scripts/td_project_docs.py"
    docs = dict(globals())
    exec(compile(docs_path.read_text(), str(docs_path), "exec"), docs)
    docs["read_project_docs"](source)

    comp = parent_comp.create(baseCOMP, "roto_python")
    comp.par.parentshortcut = "RotoPython"
    comp.viewer = True
    comp.nodeX, comp.nodeY = 0, 0
    page = comp.appendCustomPage("Connection")
    for name, label, value in (
        ("Python", "Python interpreter", source / ".venv/bin/python"),
        ("Helper", "MIDI process", source / "midi_process.py"),
    ):
        par = page.appendFile(name, label=label)[0]
        par.default = par.val = os.path.relpath(value, project.folder)
    par = page.appendStr("Device", label="Exact MIDI port name")[0]
    par.default = par.val = "Roto-Control"
    for name in ("Connect", "Disconnect"):
        page.appendPulse(name)
    page = comp.appendCustomPage("Control")
    value = page.appendFloat("Value", label="Value (Knob 1)")[0]
    value.default = value.val = 0.5
    value.min = value.normMin = 0
    value.max = value.normMax = 1
    value.clampMin = value.clampMax = True
    page.appendPulse("Offerparameter", label="Offer Value to hardware LEARN")
    kinds = {"protocol": textDAT, "RotoPythonExt": textDAT,
             "parameter_callbacks": parameterexecuteDAT, "lifecycle_callbacks": executeDAT}
    positions = {"RotoPythonExt": (-250, 0), "protocol": (-250, -170),
                 "parameter_callbacks": (-250, -340), "lifecycle_callbacks": (-250, -510)}
    for name, kind in kinds.items():
        dat = comp.create(kind, name)
        dat.viewer = True
        dat.nodeX, dat.nodeY = positions[name]
        dat.par.language = "python"
        # Builder sets the same file-sync contract as MCP set_dat_content.
        dat.text = files[name]
        dat.par.file = os.path.relpath(code_dir / f"{name}.py", project.folder)
        dat.par.syncfile = True
        dat.par.loadonstart = True

    callbacks = comp.op("parameter_callbacks")
    callbacks.par.op.expr = "parent.RotoPython"
    callbacks.par.pars = "Value Connect Disconnect Offerparameter"
    callbacks.par.custom = True
    callbacks.par.builtin = False
    callbacks.par.valuechange = True
    callbacks.par.valueschanged = False
    callbacks.par.onpulse = True
    lifecycle = comp.op("lifecycle_callbacks")
    lifecycle.par.framestart = True
    lifecycle.par.exit = True

    params = comp.create(parameterCHOP, "parameter_values")
    params.par.ops.expr = "parent.RotoPython"
    params.par.custom = True
    params.par.builtin = False
    params.par.parameter = "Value Connected Plugin Mapped Touched Rx Tx Rejected Echoblocked"
    params.viewer = True
    params.nodeX, params.nodeY = 0, 0
    output = comp.create(nullCHOP, "null_values")
    output.inputConnectors[0].connect(params)
    output.par.cooktype = "selective"
    output.viewer = True
    output.nodeX, output.nodeY = 175, 0

    upgrade_ns = dict(globals())
    upgrade_path = source / "upgrade_network.py"
    exec(compile(upgrade_path.read_text(), str(upgrade_path), "exec"), upgrade_ns)
    upgrade_ns["upgrade"](parent_comp, source)
    helper_dat = comp.create(textDAT, 'midi_process')
    helper_dat.par.language = 'python'
    helper_dat.text = (source / 'midi_process.py').read_text()
    comp.par.Helper.enable = False
    comp.par.ext0object = "op('./RotoPythonExt').module.RotoPythonExt(me)"
    comp.par.ext0promote = True
    comp.par.ext0name = ""
    comp.par.reinitextensions.pulse()
    controls_ns = dict(globals())
    controls_path = source / "upgrade_controls.py"
    exec(compile(controls_path.read_text(), str(controls_path), "exec"), controls_ns)
    controls_ns["upgrade"](parent_comp, source)
    inspector_ns = dict(globals())
    inspector_path = source / "build_inspector.py"
    exec(compile(inspector_path.read_text(), str(inspector_path), "exec"), inspector_ns)
    inspector_ns["build"](comp, source)
    docs["embed_project_docs"](comp, source)
    comp.op("readme_md").nodeX = 0
    comp.op("readme_md").nodeY = -300
    if comp.op("docs") is not None:
        comp.op("docs").nodeX = 220
        comp.op("docs").nodeY = -325
    return comp
