"""Guarded native drafts. Menu labels reconcile through the controller boundary."""
import math
from parameter_definition import snapshot
FIELDS=('label','default','normMin','normMax','min','max','clampMin','clampMax')
BOUNDS=FIELDS[2:]

def guard(par):
    if par is None or not par.valid:raise ValueError('Target unavailable; use Repair')
    if not par.isCustom:raise ValueError('Use TD Definition for built-in parameters')
    if par.style not in ('Float','Int','Menu') or len(par.parGroup)!=1 or par.sequence is not None:
        raise ValueError('Inline definition edits support scalar Float / Int / static Menu only')
    if par.style=='Menu':
        if par.menuSource:raise ValueError('Dynamic Menu source: use TD Definition')
        names=tuple(par.menuNames);labels=tuple(par.menuLabels)
        if not 2<=len(names)<=24 or len(set(names))!=len(names) or len(labels)!=len(names):
            raise ValueError('Static Menu requires 2–24 unique names and matching labels')
    if par.owner.par.clone.eval() or par.owner.clones:
        raise ValueError('Clone ownership: use TD Definition')
    if par.mode.name!='CONSTANT' or par.defaultMode.name!='CONSTANT' or par.bindReferences:
        raise ValueError('Shared / expression / Bind ownership: use TD Definition')
    if par.readOnly:raise ValueError('Read-only parameter: use TD Definition')
    return par

def fingerprint(par):
    data=snapshot(par)
    return dict(target=data['target'],native=data['native'],index=par.index,
                group=tuple(p.name for p in par.parGroup),default=par.default,label=par.label,
                limits=(par.min,par.max),slider=(par.normMin,par.normMax),order=getattr(par,'order',None),
                menu=(tuple(par.menuNames),tuple(par.menuLabels),str(par.menuSource or '')) if par.style=='Menu' else ())

def begin(info,resolve,mapping_ranges=()):
    par=guard(resolve(info))
    if par.style=='Menu':
        return dict(fingerprint=fingerprint(par),original=dict(menuLabels=tuple(par.menuLabels)),
                    style='Menu',menu_names=tuple(par.menuNames),mapping_ranges=tuple(mapping_ranges))
    return dict(fingerprint=fingerprint(par),original={key:getattr(par,key) for key in FIELDS},
                style=par.style,mapping_ranges=tuple(mapping_ranges))

def preview(draft,patch):
    if draft['style']=='Menu':
        if not isinstance(patch,dict) or set(patch)!={'menuLabels'}:raise ValueError('Edit Menu labels only')
        labels=patch['menuLabels']
        if not isinstance(labels,(tuple,list)) or len(labels)!=len(draft['menu_names']):raise ValueError('Keep all Menu choices in their original order')
        if any(not isinstance(s,str) or not s.strip() or len(s)>128 or any(ord(c)<32 for c in s) for s in labels):
            raise ValueError('Each Menu label must be 1–128 characters on one line')
        return dict(menuLabels=tuple(labels))
    if not isinstance(patch,dict) or not patch or set(patch)-set(FIELDS):raise ValueError('Invalid definition fields')
    values=dict(draft['original']);values.update(patch);label=values['label']
    if not isinstance(label,str) or not label.strip() or len(label)>128 or any(ord(c)<32 for c in label):
        raise ValueError('Label must be 1–128 characters on one line')
    for key in ('default','normMin','normMax','min','max'):
        try:value=float(values[key])
        except (TypeError,ValueError):raise ValueError(key+' must be a finite number')
        if not math.isfinite(value):raise ValueError(key+' must be a finite number')
        if draft['style']=='Int':
            if not value.is_integer():raise ValueError('Int '+key+' must be a whole number')
            value=int(value)
        values[key]=value
    if values['normMin']>=values['normMax']:raise ValueError('Slider minimum must be less than maximum')
    if values['min']>values['max']:raise ValueError('Clamp minimum must not exceed maximum')
    if any(type(values[k]) is not bool for k in ('clampMin','clampMax')):raise ValueError('Clamp switches must be ON or OFF')
    fits(values['default'],values,'Default')
    return values

def fits(value,values,label):
    if not math.isfinite(value):raise ValueError(label+' is unavailable')
    if values['clampMin'] and value<values['min'] or values['clampMax'] and value>values['max']:
        raise ValueError(label+' is outside proposed clamp limits')

def apply(info,draft,patch,resolve,mapping_ranges=(),reconcile=None):
    values=preview(draft,patch)
    par=guard(resolve(info))
    if fingerprint(par)!=draft['fingerprint']:raise ValueError('Native definition changed; reopen the draft')
    old=draft['original']
    changes={key:value for key,value in values.items() if value!=old[key]}
    if not changes:return False
    if draft['style']=='Menu':
        if tuple(mapping_ranges)!=draft['mapping_ranges']:raise ValueError('Saved mappings changed; reopen the draft')
        if reconcile is None:raise ValueError('Menu label edits require controller reconciliation')
        live=par.val;attempted=False
        try:
            par.menuLabels=list(values['menuLabels'])
            guard(par)
            if tuple(par.menuLabels)!=values['menuLabels'] or tuple(par.menuNames)!=draft['menu_names'] or par.val!=live:
                raise RuntimeError('Native Menu did not accept labels without changing choice semantics / Value')
            attempted=True;reconcile()
        except Exception as error:
            try:
                par.menuLabels=list(old['menuLabels'])
                restored=tuple(par.menuLabels)==old['menuLabels'] and tuple(par.menuNames)==draft['menu_names'] and par.val==live
            except Exception:restored=False
            repaired=True
            if attempted and restored:
                try:reconcile()
                except Exception:repaired=False
            message='Menu edit failed: '+str(error)+'; '+('native labels restored' if restored else 'native rollback incomplete')
            if not repaired:message+='; binding repair incomplete'
            raise RuntimeError(message+'; check mapping status before re-LEARN') from error
        return True
    bounds_changed=any(k in changes for k in BOUNDS)
    clamp_changed=any(k in changes for k in ('min','max','clampMin','clampMax'))
    live=None
    if bounds_changed:
        live=par.eval()
        if par.val!=live:raise ValueError('Current Value is already clamped; adjust Value before editing bounds')
        fits(live,values,'Current Value')
    if clamp_changed:
        if tuple(mapping_ranges)!=draft['mapping_ranges']:raise ValueError('Saved mapping ranges changed; reopen the draft')
        for context,id,low,high in mapping_ranges:
            try:
                fits(low,values,'Mapping minimum');fits(high,values,'Mapping maximum')
            except ValueError:
                raise ValueError('Saved Mapping '+format(low,'.6g')+'–'+format(high,'.6g')+' conflicts with clamp limits') from None
    try:
        for key,value in changes.items():setattr(par,key,value)
        if any(getattr(par,key)!=value for key,value in changes.items()):raise RuntimeError('Native definition did not accept the edit')
        if live is not None and (par.eval()!=live or par.val!=live):raise RuntimeError('Native bounds changed live Value')
    except Exception as error:
        failures=[]
        for key in reversed(tuple(changes)):
            try:
                setattr(par,key,old[key])
                if getattr(par,key)!=old[key]:failures.append(key)
            except Exception:failures.append(key)
        if live is not None and (par.eval()!=live or par.val!=live):failures.append('live Value (not overwritten)')
        if failures:raise RuntimeError('Definition edit failed; rollback incomplete: '+', '.join(failures)) from error
        raise RuntimeError('Definition edit failed; original metadata restored') from error
    return True
