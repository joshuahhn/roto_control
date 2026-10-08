"""Shared capability/command boundary; importing this module performs no writes."""
from types import MappingProxyType
from parity import registration_fingerprint

FIELDS=('Label','Destination','Minimum','Maximum','Value')

class CommandService:
    def __init__(self,model):self.model=model

    def ActivationToken(self,context):
        return (self.model.Generation,tuple(context),tuple(self.model.Status.get('Active') or self.model.ActiveContext()))

    def ActivationCapability(self,context):
        m=self.model
        reason=('Choose a controller with Device activation support' if not hasattr(m.adapter,'Activate') else
                'Context was removed' if not m.HasContext(context) else
                'Already the active Device' if self._active(context) else
                m.Status.get('ActivationReason',''))
        return MappingProxyType(dict(enabled=not reason,reason=reason))

    def Activate(self,context,token):
        m=self.model;m.Sync();context=m._context(context)
        if token!=self.ActivationToken(context):raise ValueError('Controller session or routing changed; choose Activate again')
        capability=self.ActivationCapability(context)
        if not capability['enabled']:raise ValueError(capability['reason'])
        try:
            m.adapter.Activate(context)
            if tuple(m.adapter.ActiveContext())!=context:raise ValueError('Controller did not activate the requested Device')
        finally:m.Sync()
        return True

    def _active(self,context):
        active=self.model.Status.get('Active')
        return tuple(context)==tuple(active if active is not None else self.model.ActiveContext())

    def Health(self,context,slot):
        info=self.model.Info(context,slot)
        if not info:return MappingProxyType(dict(code='unassigned',label='Unassigned',marker='·',detail='No mapping at this control'))
        error=info.get('definition_error') or info.get('error')
        if not info.get('valid') or info.get('definition_error'):
            code,label,marker,detail='invalid','Invalid','!',error or 'Target unavailable'
        elif not self._active(context):
            code,label,marker,detail='saved','Saved','◇','Saved mapping · inactive Device'
            if info.get('requires_relearn'):detail+=' · needs re-LEARN'
        elif info.get('requires_relearn'):
            code,label,marker,detail='relearn','Re-learn','!','Mapping changed · needs hardware re-LEARN'
        elif not info.get('connected'):
            code,label,marker,detail='saved','Saved','◇','Saved mapping · controller disconnected'
        elif not info.get('plugin'):
            code,label,marker,detail='pending','Pending','○','Waiting for PLUGIN connection'
        elif info.get('mapped'):
            code,label,marker,detail='mapped','Mapped','●','Acknowledged in the current hardware session'
        else:
            code,label,marker,detail='pending','Pending','○','Registered · waiting for hardware mapping ACK'
        return MappingProxyType(dict(code=code,label=label,marker=marker,detail=detail))

    def Capabilities(self,context,slot):
        info=self.model.Info(context,slot)
        common=('No mapping at this control' if not info.get('id') else
                'Browse only: activate this Device first' if not self._active(context) else '')
        invalid=info.get('definition_error') or (info.get('error') or 'Target unavailable' if not info.get('valid') else '')
        blocked='Exit LEARN before editing Value' if self.model.Learn else 'Release the control before editing' if info.get('touched') else ''
        value_reason=common or invalid or ('Pulse targets do not have an editable Value' if info.get('mode')=='pulse' else '') or ('Target unavailable' if not info.get('available') else '') or blocked
        ping_reason=common or invalid or ('Connect to PLUGIN before Ping' if not info.get('connected') or not info.get('plugin') else '') or ('Open HW LEARN, select this control, then Ping' if not self.model.Learn else '')
        clear_reason=common or ('Exit LEARN before Clear' if self.model.Learn else 'Release this control before Clear' if info.get('touched') else '')
        mapping_reason=common or invalid or ('Exit LEARN before configuring mapping' if self.model.Learn else 'Release the control before configuring mapping' if info.get('touched') else '')
        if info.get('binding_type')=='value':mapping_reason=mapping_reason or 'Mapping configuration requires a collection'
        assign_reason=('Browse only: activate this Device first' if not self._active(context) else
                       'Release the control before assigning' if info.get('touched') else
                       'Choose a controller with target assignment support' if not hasattr(self.model.adapter,'Assign') else '')
        return MappingProxyType({name:MappingProxyType(dict(enabled=not reason,reason=reason)) for name,reason in [('value',value_reason),('ping',ping_reason),('clear',clear_reason),('mapping',mapping_reason),('assign',assign_reason)]})

    def ValueSchema(self,context,slot):
        info=self.model.Info(context,slot);style=info.get('parameter_style','')
        kind='pulse' if info.get('mode')=='pulse' else 'menu' if style=='Menu' else 'toggle' if style=='Toggle' or info.get('mode')=='toggle' else 'integer' if style=='Int' else 'float'
        return MappingProxyType(dict(kind=kind,names=tuple(info.get('menu_names',())),labels=tuple(info.get('menu_labels',())),reason=self.Capabilities(context,slot)['value']['reason']))

    def Assign(self,context,slot,handle,token):
        context,slot,info=self._target(context,slot,token)
        self._require(context,slot,'assign')
        result=self.model.adapter.Assign(context,slot,handle)
        self.model.RefreshDefinitions(context,slot);self.model.Sync()
        return result

    def ParameterDefinition(self,context,slot,token):
        context,slot,info=self._target(context,slot,token)
        return self.model.adapter.ParameterDefinition(info,self.model.Learn,bool(info.get('touched')))

    def OpenNativeEditor(self,context,slot,token,kind):
        context,slot,info=self._target(context,slot,token)
        return self.model.adapter.OpenNativeEditor(info,kind,self.model.Learn,bool(info.get('touched')))

    def DefinitionDraft(self,context,slot,token):
        context,slot,info=self._target(context,slot,token)
        if not self._active(context):raise ValueError('Browse only: activate this Device first')
        return self.model.adapter.DefinitionDraft(context,info)

    def PreviewStyle(self,context,slot,token,draft,patch):
        context,slot,info=self._target(context,slot,token)
        if not self._active(context):raise ValueError('Browse only: activate this Device first')
        return self.model.adapter.PreviewStyle(context,info,draft,patch)

    def ApplyDefinition(self,context,slot,token,draft,patch):
        context,slot,info=self._target(context,slot,token)
        if not self._active(context):raise ValueError('Browse only: activate this Device first')
        result=self.model.adapter.ApplyDefinition(context,info,draft,patch)
        self.model.RefreshDefinitions();self.model.Sync()
        return result

    def MappingSchema(self,context,slot):
        info=self.model.Info(context,slot);style=info.get('parameter_style','')
        button=info.get('kind')=='button'
        modes=('value',) if not button else ('cycle',) if style=='Menu' else ('toggle',) if style=='Toggle' else ('pulse',) if style=='Pulse' else ('toggle','pulse')
        values=dict(minimum=info.get('minimum',0.),maximum=info.get('maximum',1.),mode=info.get('mode',modes[0]),button_type=info.get('button_type') if button else None)
        return MappingProxyType(dict(values=MappingProxyType(values),modes=modes,inputs=('toggle','push') if button else (),range_editable=bool(info and not button and style!='Menu'),integer=style=='Int',style=style or 'Callback',reason=self.Capabilities(context,slot)['mapping']['reason']))

    def Configure(self,context,slot,patch,token):
        context,slot,info=self._target(context,slot,token)
        self._require(context,slot,'mapping');schema=self.MappingSchema(context,slot)
        if not isinstance(patch,dict) or not patch or set(patch)-set(schema['values']):raise ValueError('Invalid mapping fields')
        values=dict(schema['values']);values.update(patch)
        for name in ('minimum','maximum'):values[name]=self.model._number(values[name])
        if values['minimum']>=values['maximum']:raise ValueError('Minimum must be less than Maximum')
        if values['mode'] not in schema['modes']:raise ValueError('Mode is incompatible with this target Style')
        if values['button_type'] not in (schema['inputs'] or (None,)):raise ValueError('Input type is incompatible with this control')
        if not schema['range_editable'] and any(values[n]!=schema['values'][n] for n in ('minimum','maximum')):raise ValueError('This target has a fixed mapping Range')
        if schema['integer'] and any(not values[n].is_integer() for n in ('minimum','maximum')):raise ValueError('Integer mapping limits must be integers')
        if values==dict(schema['values']):return False
        # One validated API call owns mutation, rollback and re-LEARN semantics.
        self.model.adapter.Configure(context,info,values);self.model.Sync();return True

    def _target(self,context,slot,token):
        m=self.model;context=m._context(context);slot=m._slot(slot)
        m.RefreshDefinitions(context,slot);m.Sync();context=m._context(context)
        if token!=m.GetToken(context,slot):
            # Catalog owns the exception type; avoid a cross-COMP DAT import.
            m._reject_stale()
        return context,slot,m.Info(context,slot)

    def _require(self,context,slot,action):
        capability=self.Capabilities(context,slot)[action]
        if not capability['enabled']:raise ValueError(capability['reason'])

    def Commit(self,context,slot,record,token):
        context,slot,info=self._target(context,slot,token)
        m=self.model;old=m.GetCatalog(context)[slot];values=dict(record)
        if set(values)!=set(FIELDS):raise ValueError('Invalid fields')
        if any(values[n]!=old[n] for n in FIELDS if n!='Value'):
            raise ValueError('Mapping metadata is read-only in this prototype')
        self._require(context,slot,'value')
        value=m._number(values['Value'])
        schema=self.ValueSchema(context,slot)
        if schema['kind'] in ('integer','menu','toggle') and not value.is_integer():raise ValueError('Value must be an integer')
        if schema['kind']=='menu' and not 0<=value<len(schema['names']):raise ValueError('Menu option is unavailable')
        if schema['kind']=='toggle' and value not in (0,1):raise ValueError('Toggle Value must be 0 or 1')
        if not old['Minimum']<=value<=old['Maximum']:raise ValueError('Value is outside the range')
        if value==old['Value']:return False
        m.adapter.Write(context,info,value);m.Sync()
        return True

    def Ping(self,context,slot,token):
        context,slot,info=self._target(context,slot,token)
        self._require(context,slot,'ping')
        if not self.model.adapter.Ping(context,info):raise ValueError('Ping rejected; check hardware LEARN')
        self.model.Sync();return True

    def CheckClear(self,context,slot,token):
        context,slot,info=self._target(context,slot,token)
        self._require(context,slot,'clear')
        return context,info

    def Clear(self,context,slot,token):
        context,info=self.CheckClear(context,slot,token)
        self.model.adapter.Clear(context,info);self.model.Sync();return True

    def _device(self,context):
        m=self.model;context=m._context(context)
        m.RefreshDefinitions(context);m.Sync()
        if not self._active(context):raise ValueError('Browse only: activate this Device before Clear Device')
        if m.Learn:raise ValueError('Exit LEARN before Clear Device')
        info=tuple(m.Info(context,i) for i in range(16))
        if m.Status.get('Touched') or any(r.get('touched') for r in info):raise ValueError('Release all controls before Clear Device')
        if not hasattr(m.adapter,'ClearDevice'):raise ValueError('Controller does not support Clear Device')
        return context,info

    def PrepareClearDevice(self,context):
        context,info=self._device(context)
        ids=tuple(r['id'] for r in info if r.get('id'))
        if not ids:raise ValueError('This Device has no registrations to clear')
        return dict(context=context,generation=self.model.Stats()['generation'],fingerprint=registration_fingerprint(info),ids=ids)

    def ClearDevice(self,context,confirmation):
        current=self.PrepareClearDevice(context)
        if confirmation!=current:raise ValueError('Device registrations/session changed; confirm again')
        error=''
        try:self.model.adapter.ClearDevice(tuple(context))
        except Exception as failure:error=str(failure)
        self.model.RefreshDefinitions(context);self.model.Sync()
        remaining=tuple(self.model.Info(context,i).get('id') for i in range(16) if self.model.Info(context,i).get('id'))
        removed=tuple(id for id in current['ids'] if id not in remaining)
        return dict(removed=removed,remaining=remaining,error=error)

class InspectorCommands:
    """TD extension proxy resolves the current model after reload/reinitialization."""
    def __init__(self,ownerComp):self.ownerComp=ownerComp
    def _service(self):
        model=self.ownerComp.par.Model.eval()
        if not model:raise ValueError('Choose the shared Inspector model')
        return model.ext.InspectorModel._commands
    def ActivationToken(self,*args):return self._service().ActivationToken(*args)
    def ActivationCapability(self,*args):return self._service().ActivationCapability(*args)
    def Activate(self,*args):return self._service().Activate(*args)
    def Health(self,*args):return self._service().Health(*args)
    def Capabilities(self,*args):return self._service().Capabilities(*args)
    def MappingSchema(self,*args):return self._service().MappingSchema(*args)
    def ValueSchema(self,*args):return self._service().ValueSchema(*args)
    def ParameterDefinition(self,*args):return self._service().ParameterDefinition(*args)
    def OpenNativeEditor(self,*args):return self._service().OpenNativeEditor(*args)
    def DefinitionDraft(self,*args):return self._service().DefinitionDraft(*args)
    def PreviewStyle(self,*args):return self._service().PreviewStyle(*args)
    def ApplyDefinition(self,*args):return self._service().ApplyDefinition(*args)
    def Assign(self,*args):return self._service().Assign(*args)
    def Configure(self,*args):return self._service().Configure(*args)
    def Commit(self,*args):return self._service().Commit(*args)
    def Ping(self,*args):return self._service().Ping(*args)
    def CheckClear(self,*args):return self._service().CheckClear(*args)
    def Clear(self,*args):return self._service().Clear(*args)
    def PrepareClearDevice(self,*args):return self._service().PrepareClearDevice(*args)
    def ClearDevice(self,*args):return self._service().ClearDevice(*args)
