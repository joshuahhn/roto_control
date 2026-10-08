"""Independent Mapping draft. Value drafts remain in the existing view backing."""
class MappingDraft:
    def __init__(self):self.Close()
    def Close(self):self.open=False;self.token=None;self.original=None;self.message=''
    def Open(self,model,context,slot):
        model.Inspect(context,slot)
        self.original=dict(model.MappingSchema(context,slot)['values'])
        self.token=model.GetToken(context,slot);self.open=True;self.message=''
        return dict(self.original)
    def IsStale(self,model,context,slot):return self.token!=model.GetToken(context,slot)
    def Status(self,model,context,slot):
        if self.message!='Mapping saved · needs re-LEARN':return self.message
        if self.IsStale(model,context,slot):return 'Mapping changed · reopen section'
        info=model.Info(context,slot)
        if info.get('requires_relearn'):return self.message
        return 'Mapping saved · hardware acknowledged' if info.get('mapped') else 'Mapping saved · awaiting hardware ACK'
    def Apply(self,model,context,slot,values):
        changed=model.Configure(context,slot,dict(values),self.token)
        fresh=self.Open(model,context,slot)
        self.message=('Mapping saved · needs re-LEARN' if model.Info(context,slot).get('requires_relearn') else 'Mapping saved' if changed else 'Mapping unchanged')
        return changed,fresh
