"""Forward native callbacks to cloned Lister; capture cell-local confirmation hit."""
def native():
    return parent.RotoInspector.op('lister/internalCallbacks').module


def onSelect(comp, startrow, startcol, startcoords, endrow, endcol, endcoords, start, end):
    inspector=parent.RotoInspector
    lister=comp.ext.ListerExt
    data=lister.Data
    is_clear = (startrow is not None and startcol is not None and 0 < startrow < len(data)
                and lister.colDefine[0,startcol+1].val in ('ClearLearn','Learn','Mode','COMP','Parameter'))
    if is_clear:
        if start:
            inspector.store('clear_press',(startrow,startcol,data[startrow]['ID']))
        elif end:
            press=inspector.fetch('clear_press',None)
            inspector.store('clear_press',None)
            if (press and endrow==press[0] and endcol==press[1] and endcoords is not None
                    and 0 < endrow < len(data) and data[endrow]['ID']==press[2]):
                inspector.store('clear_hit',(endrow,endcol,endcoords.u))
                inspector.op('listerConfig/callbacks').module.onClick(dict(
                    ownerComp=comp,row=endrow,col=endcol,colName=lister.colDefine[0,startcol+1].val,rowData=data[endrow]))
        # Bypass Lister selection/double-click bookkeeping for action cells.
        return
    return native().onSelect(comp,startrow,startcol,startcoords,endrow,endcol,endcoords,start,end)


def onInitCell(*args): return native().onInitCell(*args)
def onInitRow(*args): return native().onInitRow(*args)
def onInitCol(*args): return native().onInitCol(*args)
def onInitTable(*args): return native().onInitTable(*args)
def onRollover(*args): return native().onRollover(*args)
def onRadio(*args): return native().onRadio(*args)
def onFocus(*args): return native().onFocus(*args)
def onEdit(*args): return native().onEdit(*args)
def onHover(*args): return native().onHover(*args)
def onDrop(*args): return native().onDrop(*args)
