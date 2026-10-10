"""Lossless scalar Float/Int migration; native/controller effects are explicit seams."""
from copy import deepcopy
from posixpath import normpath
import math
from definition_edit import guard,fingerprint,FIELDS,fits,preview as field_preview

EXTRA=('startSection','enable','enableExpr','readOnly','hidden','styleCloneImmune','password',
       'help','expr','bindExpr','defaultExpr','defaultBindExpr')
DEFAULTS=dict(startSection=False,enable=True,enableExpr='',readOnly=False,hidden=False,
              styleCloneImmune=False,password=False,help='',expr='',bindExpr='',defaultExpr='',defaultBindExpr='')


def begin(par):
    guard(par)
    if getattr(par,'hidden',False):raise ValueError('Hidden parameters require TD Definition')
    if par.style not in ('Float','Int'):raise ValueError('Style migration supports scalar Float / Int only')
    return dict(fingerprint=fingerprint(par),style=par.style,page=par.page.name,name=par.name,
                order=getattr(par,'order',None),metadata={n:getattr(par,n,DEFAULTS.get(n)) for n in FIELDS+EXTRA})


def plan(par,draft,patch,ranges):
    guard(par)
    if begin(par)!=draft:raise ValueError('Native definition changed; reopen Style draft')
    style=patch.get('style',draft['style'])
    if style not in ('Float','Int'):raise ValueError('Style supports Float / Int only')
    fields={k:v for k,v in patch.items() if k in FIELDS}
    if set(patch)-set(FIELDS)-{'style','style_value'}:raise ValueError('Invalid Style fields')
    native=dict(style=style,original={k:draft['metadata'][k] for k in FIELDS})
    values=field_preview(native,fields or native['original'])
    value=par.eval()
    if value!=par.val:raise ValueError('Current Value is already clamped; adjust Value first')
    if not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('Current Value is unavailable')
    if style=='Int':
        if not float(value).is_integer():raise ValueError('Int Style would lose decimals; set a whole Value first')
        for context,id,low,high in ranges:
            if not float(low).is_integer() or not float(high).is_integer():
                raise ValueError('Int Style requires whole Mapping Range endpoints; edit Mapping first')
    fits(value,values,'Current Value')
    for context,id,low,high in ranges:
        fits(low,values,'Mapping minimum');fits(high,values,'Mapping maximum')
    result=dict(style=style,value=int(value) if style=='Int' else float(value),metadata=dict(draft['metadata'],**values),
                changed=style!=draft['style'],mappings=len(ranges))
    return result


class ParameterPreview:
    """Read-only candidate for Controls validation before native setters."""
    def __init__(self,par,candidate):self._par=par;self._candidate=candidate
    def __getattr__(self,name):
        if name=='style':return self._candidate['style']
        if name=='val':return self._candidate['value']
        if name in self._candidate['metadata']:return self._candidate['metadata'][name]
        return getattr(self._par,name)
    def eval(self):return self._candidate['value']


def replace_native(par,style,draft,metadata,value):
    """No destroy: replace in place, then restore all supported metadata."""
    current=getattr(par.page,'append'+style)(draft['name'],label=metadata['label'],order=draft['order'],replace=True)[0]
    current.clampMin=current.clampMax=False
    # Expression members can change mode. Restore dormant strings before the
    # original CONSTANT modes; evaluation/default ownership was preflighted.
    for name in ('expr','bindExpr','defaultExpr','defaultBindExpr'):
        setattr(current,name,metadata[name] or '')
    current.mode=ParMode.CONSTANT
    current.defaultMode=ParMode.CONSTANT
    for name in ('label','default','normMin','normMax','min','max','startSection','enable',
                 'styleCloneImmune','password','help'):
        setattr(current,name,metadata[name])
    current.enableExpr=metadata['enableExpr'] or ''
    current.val=value
    current.clampMin=metadata['clampMin'];current.clampMax=metadata['clampMax']
    current.readOnly=metadata['readOnly']
    return current


def check(par,original,style,draft,metadata,value):
    guard(par)
    if (par.style!=style or par.index!=draft['fingerprint']['index'] or not original.isSamePar(par)
            or par.name!=draft['name'] or par.page.name!=draft['page'] or par.order!=draft['order']):
        raise RuntimeError('Style replacement did not retain native parameter identity / location')
    for key,expected in metadata.items():
        actual=getattr(par,key)
        # TD uses None and empty string interchangeably for absent expressions.
        if key in ('expr','bindExpr','defaultExpr','defaultBindExpr','enableExpr'):actual=actual or '';expected=expected or ''
        if actual!=expected:raise RuntimeError('Style replacement changed '+key)
    if par.val!=value or par.eval()!=value:raise RuntimeError('Style replacement changed live Value')


def apply(par,draft,patch,ranges,reconcile,compensate,replace=replace_native):
    candidate=plan(par,draft,patch,ranges)
    if not candidate['changed']:return False
    if 'style_value' not in patch or patch['style_value']!=candidate['value']:
        raise ValueError('Value moved or Style preview missing; refresh Style preview')
    value=par.val;attempted=False
    try:
        current=replace(par,candidate['style'],draft,candidate['metadata'],candidate['value'])
        check(current,par,candidate['style'],draft,candidate['metadata'],candidate['value'])
        attempted=True;reconcile()
    except Exception as error:
        failures=[]
        try:
            restored=replace(par,draft['style'],draft,draft['metadata'],value)
            check(restored,par,draft['style'],draft,draft['metadata'],value)
        except Exception as restore_error:failures.append('native: '+str(restore_error))
        if attempted:
            try:compensate()
            except Exception as restore_error:failures.append('bindings: '+str(restore_error))
        message='Style migration failed: '+str(error)+'; '
        message+=('rollback incomplete: '+'; '.join(failures)) if failures else 'original definition restored'
        raise RuntimeError(message+'; check hardware re-LEARN status') from error
    return True


def matches(record,comp,parameter,controller_path):
    path=record.get('comp','')
    return bool(isinstance(path,str) and record.get('parameter')==parameter and
                normpath(path if path.startswith('/') else controller_path+'/'+path)==comp)


def rewrite_library(data,page_targets,comp,parameter,controller_path,identity_for,style):
    """Detached candidate: retain every registration and change related identities."""
    registry=deepcopy(data);pages=deepcopy(page_targets);changed=set();count=0
    def target(record,pending):
        nonlocal count
        count+=1
        if count>16384:raise ValueError('Style library exceeds bounded rewrite limit')
        if not matches(record,comp,parameter,controller_path):return False
        if record.get('kind')!='knob' or record.get('mode')!='value':raise ValueError('Related registration is incompatible with Float / Int Style')
        record['identity']=identity_for(record);record['parameter_style']=style
        record['menu_names']=[];record['menu_labels']=[]
        pending.add(record['id']);changed.add(record['id']);return True
    for layout in registry.get('records',[]):
        for track in layout['tracks']:
            for plugin in track['plugins']:
                state=plugin['state'];pending=set(state.get('needs_relearn',()))
                related=False
                for record in plugin['targets']:related=target(record,pending) or related
                for key in ('page_targets','parameter_assignments'):
                    for record in state.get(key,[]):related=target(record,pending) or related
                for record in state.get('control_catalog',[]):
                    if matches(record,comp,parameter,controller_path):
                        record.update(parameter_style=style,requires_relearn=True,mapped=False,last_mapped=False)
                if related:state['needs_relearn']=tuple(sorted(pending))
    pending=set()
    for record in pages:target(record,pending)
    return registry,pages,tuple(sorted(pending))
