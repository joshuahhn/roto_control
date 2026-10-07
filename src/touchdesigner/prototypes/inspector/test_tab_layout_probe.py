from types import SimpleNamespace
from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from tab_layout_probe import Decode,Recorder,Start,Stop,Save
from parity import detail_groups

def packet(group,command,*data):return (240,0,34,3,2,group,command,*data,247)

class ProbeTests(TestCase):
    def test_track_device_page_and_mix_have_distinct_wire_families(self):
        for group,command,name in [(10,9,'SELECT_TRACK'),(11,7,'SELECT_DEVICE'),(10,20,'PAGE_LEFT'),(12,2,'SET_MIXER_SELECTED_MODE')]:
            self.assertEqual(Decode(packet(group,command,0))['name'],name)
        self.assertEqual(Decode(packet(11,99,0))['name'],'UNKNOWN')
        for message in [(191,12,127),packet(10,24,1),packet(11,15,1),(240,1,2,247),packet(11,7,128)]:self.assertIsNone(Decode(message))
    def test_recorder_bounds_and_snapshot_failures_do_not_break_dispatch(self):
        r=Recorder(lambda:dict(key='A'),capacity=2)
        for i in range(5):r.Event('marker',i)
        self.assertEqual(len(r.Report()['events']),2);self.assertEqual(r.dropped,3)
        r.snapshot=lambda:(_ for _ in ()).throw(RuntimeError('Probe only'))
        r.Event('marker','failure');self.assertEqual(r.errors,1)
    def test_live_hooks_preserve_arguments_results_and_restore_methods(self):
        class Host:
            def send(self,*args,**kwargs):calls.append(('tx',args,kwargs));return 'sent'
        class Ext:
            def __init__(self):self._host=Host()
            def _receive_midi(self,*args,**kwargs):calls.append(('rx',args,kwargs));return 'received'
        class Controller:
            path='/fixture'
            def GetLayoutContext(self):return dict(legacy=True)
            def GetControlCatalog(self):return []
            @property
            def State(self):return dict(Connected=True,Plugin=True,Learning=False)
        calls=[];c=Controller();ext=Ext();c.ext=SimpleNamespace(RotoPythonExt=ext)
        with TemporaryDirectory() as directory:
            Start(c,Path(directory)/'trace.json')
            self.assertEqual(ext._receive_midi(packet(11,7,0),('epoch',3)), 'received')
            self.assertEqual(ext._host.send(packet(10,7,0)), 'sent')
            self.assertEqual(calls[0][1][1],('epoch',3))
            report=Stop(c)
            self.assertEqual([e['kind'] for e in report['events']],['start','rx_before','rx_after','queued_tx','stop'])
            self.assertEqual(report['restore_conflicts'],[])
            self.assertNotIn('_receive_midi',vars(ext));self.assertNotIn('send',vars(ext._host))
            self.assertIsNone(Stop(c))
    def test_probe_stop_does_not_overwrite_a_later_hook(self):
        c=SimpleNamespace(path='/fixture',ext=SimpleNamespace(RotoPythonExt=SimpleNamespace(_host=SimpleNamespace(send=lambda p:None),_receive_midi=lambda p:None)),GetLayoutContext=lambda:dict(legacy=True),GetControlCatalog=lambda:[],State=dict(Connected=True,Plugin=True,Learning=False))
        with TemporaryDirectory() as directory:
            Start(c,Path(directory)/'trace.json');replacement=lambda p:'replacement';c.ext.RotoPythonExt._receive_midi=replacement
            self.assertEqual(Stop(c)['restore_conflicts'],['_receive_midi'])
            self.assertIs(c.ext.RotoPythonExt._receive_midi,replacement)
    def test_item_and_native_list_hooks_preserve_rejection_and_restore(self):
        panel=SimpleNamespace(click=SimpleNamespace(val=2),inside=SimpleNamespace(val=1),focusselect=SimpleNamespace(val=1))
        native=SimpleNamespace(ownerComp=SimpleNamespace(panel=panel),_clickedOnce=True,
                               onSelect=lambda *a,**k:'native result',DoubleClick=lambda *a,**k:'double result')
        menu=SimpleNamespace(Lister=SimpleNamespace(ext=SimpleNamespace(ListerExt=native)))
        view=SimpleNamespace(ownerComp=SimpleNamespace(path='/view'),Key=lambda:('L','T','D'),_follow_routing=True,
                             OpenContextMenu=lambda name:True,SelectContextMenu=lambda info:False)
        c=SimpleNamespace(path='/fixture',ext=SimpleNamespace(RotoPythonExt=SimpleNamespace(_host=SimpleNamespace(send=lambda p:None),_receive_midi=lambda p:None)),GetLayoutContext=lambda:dict(legacy=True),GetControlCatalog=lambda:[],State=dict(Connected=True,Plugin=True,Learning=False))
        original_select=view.SelectContextMenu;original_native=native.onSelect
        with TemporaryDirectory() as directory:
            Start(c,Path(directory)/'trace.json',views=(view,),menu=menu)
            self.assertFalse(view.SelectContextMenu(dict(item='D',details=dict(name='Device',generation=2))))
            self.assertEqual(native.onSelect(1,0,(0,0),1,0,(0,0),False,True),'native result')
            self.assertEqual(native.DoubleClick(1,0),'double result')
            report=Stop(c)
            events={e['kind']:e['data'] for e in report['events']}
            self.assertFalse(events['item_callback_after']['accepted'])
            self.assertEqual(events['native_list_selection']['click'],2)
            self.assertTrue(events['native_list_selection']['end'])
            self.assertIn('native_double_click',events)
            self.assertIs(view.SelectContextMenu,original_select);self.assertIs(native.onSelect,original_native)
            self.assertEqual(report['restore_conflicts'],[])
    def test_details_separate_human_routing_from_long_technical_ids(self):
        info=dict(id='stable.long.id',comp='/tool',parameter='Amount',parameter_style='Float',mode='value')
        groups=detail_groups(info,dict(label='Mapped'),dict(Follow=True,FollowStatus='ready'),dict(state=dict(Rx=2,Tx=3,Rejected=0)),('L','T','tool'),('L','T','tool'),('T','tool'),True)
        self.assertEqual([title for title,rows in groups],['Mapping','Hardware routing','Technical · Refresh snapshot'])
        self.assertEqual(dict((k,v) for k,v,kind in groups[1][1])['Track · FUNC'],'T')
        self.assertNotIn('stable.long.id',str(groups[:2]));self.assertIn('stable.long.id',str(groups[2]))
        groups=detail_groups(dict(info,error='Target missing'),dict(label='Invalid'),{},None,('L','T','tool'),('L','T','tool'),('T','tool'),False)
        self.assertIn(('Issue','Target missing','long'),groups[0][1])
