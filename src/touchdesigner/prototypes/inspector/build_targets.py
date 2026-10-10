"""Install shared target discovery and reusable picker/typed widgets."""
from pathlib import Path

source_dir=Path(globals().get('inspector_source_dir',Path(project.folder)/'prototypes/inspector'))
model=globals().get('model_comp') or op('/inspector_model')
targets=model.op('base_targets') or model.create(baseCOMP,'base_targets')
targets.viewer=True;targets.par.parentshortcut='InspectorTargets'
targets.nodeX=1105;targets.nodeY=-40;targets.nodeWidth=160;targets.nodeHeight=130
if not hasattr(targets.par,'Model'):targets.appendCustomPage('Data').appendOP('Model')
targets.par.Model.expr='parent.InspectorModel'
module=targets.op('TargetCatalog') or targets.create(textDAT,'TargetCatalog')
module.viewer=True;module.par.language='python';module.text=(source_dir/'target_catalog.py').read_text()
module.nodeX=0;module.nodeY=0
targets.par.ext0object="op('./TargetCatalog').module.InspectorTargets(me)"
targets.par.ext0promote=True;targets.par.initextonstart=True;targets.initializeExtensions(0)

if not globals().get('targets_only',False):
    # Reuse the existing panel-building helpers, without rerunning its migration.
    definition=(source_dir/'build_mapping.py').read_text().split('for view in views:')[0]
    # Reuse helper functions in one namespace.
    helpers=dict(globals());exec(definition,helpers)
    panel,text,button=[helpers[n] for n in ('panel','text','button')]

    def anchors(o,left=12,right=-12):
        o.par.x.expr='';o.par.w.expr='';o.par.hmode='anchors'
        o.par.leftanchor=0;o.par.rightanchor=1;o.par.leftoffset=left;o.par.rightoffset=right

    for view in (globals()['target_views'] if 'target_views' in globals() else [op('/inspector_below'),op('/inspector_popup')]):
        if not view:continue
        draft=view.op('base_draft');page=draft.customPages[0]
        for name in ('Pickscope','Pickquery'):
            if not hasattr(draft.par,name):page.appendStr(name)
        host=view.op('ui').module.popup_host(view)
        for editor in (view.op('container_scroll/container_content/editor_below'),host.op('container_editor_content')):
            target=editor.op('field_Destination');target.par.clickthrough=False
            target.par.placeholdertext='Choose target ▾'
            cb=editor.op('click_target') or editor.create(panelexecuteDAT,'click_target')
            cb.viewer=True;cb.par.language='python';cb.par.panels='field_Destination';cb.par.panelvalue='lselect';cb.par.offtoon=True
            cb.text="def onOffToOn(panelValue):\n    parent.InspectorDemo.Action('target_picker')\n"
            for kind in ('menu','toggle'):
                b=button(editor,'value_'+kind,'','value_'+kind,62,36,136,22);anchors(b,62,-12);b.par.display=False
            b=button(editor,'value_type','Float ↔','value_type',0,36,48,22)
            b.par.hmode='anchors';b.par.leftanchor=b.par.rightanchor=1;b.par.leftoffset=-60;b.par.rightoffset=-12
            b.op('text_label').par.fontsize=9;b.par.display=False
            section=panel(editor,containerCOMP,'container_picker',0,6,210,244);anchors(section,0,0);section.par.display=False
            text(section,'label_scope','Scope',12,216,44,22)
            text(section,'label_search','Search',12,188,44,22)
            for name,y in [('scope',216),('query',188)]:
                f=text(section,'field_'+name,'',62,y,136,22);anchors(f,62,-12)
                f.par.bgalpha=1;f.par.bgcolorr=f.par.bgcolorg=f.par.bgcolorb=.08
                f.par.clickthrough=False;f.par.editmode='editablecontinuous' if name=='query' else 'editable'
                f.par.textpaddingl=f.par.textpaddingr=6
                f.par.text.bindExpr="parent.InspectorDemo.op('base_draft').par.Pick%s"%name
                callback=f.par.callbacks.eval();callback.par.language='python'
                if name=='query':
                    callback.text="def onTextEdit(comp):parent.InspectorDemo.PickerQuery(comp.editText)\ndef onTextEditEnd(comp,value,prevValue):parent.InspectorDemo.PickerQuery(value)\ndef onValueChange(comp,value,prevValue):pass\n"
                else:
                    callback.text="def onTextEditEnd(comp,value,prevValue):parent.InspectorDemo.SearchTargets(True)\ndef onValueChange(comp,value,prevValue):pass\n"
            t=text(section,'text_count','',12,166,186,18,9);anchors(t)
            for i in range(6):
                b=button(section,'row'+str(i),'','picker_row'+str(i),12,142-i*22,186,20);anchors(b)
                b.op('text_label').par.alignx='left';b.op('text_label').par.textpaddingl=6
            t=text(section,'text_status','',12,6,102,18,9);anchors(t,12,-144);t.par.type='multiline';t.par.wordwrap=True;t.par.h=24
            for name,action,icon,right in [('prev','picker_prev','\U000f0141',108),('next','picker_next','\U000f0142',78),('cancel','picker_cancel','cancel',48),('assign','picker_assign','apply',18)]:
                b=button(section,name,'',action,0,6,24,24)
                b.par.hmode='anchors';b.par.leftanchor=b.par.rightanchor=1;b.par.leftoffset=-right-24;b.par.rightoffset=-right
                label=b.op('text_label')
                if icon in ('cancel','apply'):view.op('ui').module.action_icon(label,icon)
                else:label.par.font='Material Design Icons';label.par.fontsize=15;label.par.text=icon
            # Use an explicit Refresh label so Ping keeps its signal meaning.
            refresh=button(section,'refresh','Refresh','picker_refresh',0,166,48,18)
            refresh.par.hmode='anchors';refresh.par.leftanchor=refresh.par.rightanchor=1;refresh.par.leftoffset=-60;refresh.par.rightoffset=-12
            anchors(section.op('text_count'),12,-66)
            for o in section.findChildren(maxDepth=2)+[editor.op('value_menu'),editor.op('value_toggle')]:
                if o.OPType in ('containerCOMP','textCOMP'):
                    o.par.fit='off';o.par.scalex=o.par.scaley=1
                    if o.OPType=='textCOMP':o.par.scaletofit='never';o.par.fontsizeunits='panelunits'
            for parent in [section]+[editor.op(n) for n in ('value_menu','value_toggle')]:
                for i,o in enumerate(parent.children):o.nodeX=(i%5)*200;o.nodeY=-(i//5)*160+130-o.nodeHeight
print('Shared target discovery and compact typed widgets installed')
