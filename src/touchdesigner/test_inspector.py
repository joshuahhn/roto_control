"""Inspector shows active mappings independently of saved target registration."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).parent/'code/py/roto_python/inspector'))
from inspector_data import refresh, request_clear, confirm_clear, confirmation_choice

class InspectorTests(unittest.TestCase):
    def inspector(self):
        table=SimpleNamespace(text='')
        title=SimpleNamespace(par=SimpleNamespace(text=''))
        return SimpleNamespace(op=lambda name:table if name=='targets' else title if name=='title' else None,
                               fetch=lambda key,default=None:default, store=lambda key,value:None),table
    def state(self,**changes):
        return dict(dict(kind='knob',slot=1,valid=True,mapped=True,comp='/scene',binding_type='parameter',parameter='Speed',mode='value',button_type=None,value=6.12345,id='scene.speed',error='',minimum=0,maximum=10,connected=True,plugin=True),**changes)
    def row(self,table):
        lines=table.text.splitlines()
        return dict(zip(lines[0].split('\t'),lines[1].split('\t')))
    def test_disconnect_retains_database_destination_and_value(self):
        inspector,table=self.inspector()
        state=self.state(mapped=False)
        refresh(inspector,[state])
        row=self.row(table)
        self.assertEqual([row[k] for k in ('Mapped','COMP','Parameter','Value')],['No','/scene','Speed','6.123'])
        self.assertEqual(row['ID'],'scene.speed')
        self.assertEqual((state['comp'],state['parameter'],state['value']),('/scene','Speed',6.12345))
        refresh(inspector,[self.state()])
        row=self.row(table)
        self.assertEqual([row[k] for k in ('COMP','Parameter','Value')],['/scene','Speed','6.123'])
    def test_learn_labels_and_empty_slot_column_count(self):
        for changes,label in [({'mapped':False},'Learn'),({'mapped':True},'Re-learn'),({'mapped':False,'requires_relearn':True},'Re-learn')]:
            inspector,table=self.inspector();refresh(inspector,[self.state(**changes)])
            self.assertEqual(self.row(table)['Learn'],label)
            self.assertTrue(all(len(row.split('\t'))==13 for row in table.text.splitlines()))

    def test_invalid_and_unmapped_targets_keep_catalog_data(self):
        for state in [self.state(valid=False,mapped=False,error='Missing target'),self.state(mapped=False,binding_type='callback',comp='',parameter='')]:
            inspector,table=self.inspector();refresh(inspector,[state])
            row=self.row(table);self.assertEqual(row['COMP'],'Python callback' if state['binding_type']=='callback' else '/scene')
            self.assertEqual(row['Error'],state['error'])
        inspector,table=self.inspector();refresh(inspector,[self.state(binding_type='callback',comp='',parameter='')])
        self.assertEqual(self.row(table)['COMP'],'Python callback')

class ConfirmationTests(unittest.TestCase):
    inspector=InspectorTests.inspector
    state=InspectorTests.state
    row=InspectorTests.row
    def fixture(self):
        storage={}; calls=[]; states=[self.state()]
        controller=SimpleNamespace(GetControlStates=lambda:states,GetControlCatalog=lambda:states,RemoveControl=lambda id:calls.append(id),RemoveAllControls=lambda:calls.append('ALL'))
        inspector,table=self.inspector()
        inspector.fetch=lambda key,default=None:storage.get(key,default)
        inspector.store=lambda key,value:storage.update({key:value})
        inspector.parent=lambda:controller
        return inspector,table,states,calls

    def test_row_confirmation_cancel_and_accept(self):
        inspector,table,states,calls=self.fixture()
        request_clear(inspector,'scene.speed');self.assertEqual(calls,[])
        self.assertIn('[ Yes ]',self.row(table)['ClearLearn'])
        confirm_clear(inspector,False,'scene.speed');self.assertEqual(calls,[])
        request_clear(inspector,'scene.speed');confirm_clear(inspector,True,'scene.speed')
        self.assertEqual(calls,['scene.speed'])
        confirm_clear(inspector,True,'scene.speed');self.assertEqual(calls,['scene.speed'])

    def test_confirmation_gap_does_not_confirm(self):
        self.assertTrue(confirmation_choice(.2))
        self.assertFalse(confirmation_choice(.8))
        self.assertIsNone(confirmation_choice(.5))
        self.assertIsNone(confirmation_choice(-1))

    def test_all_and_stale_identity(self):
        inspector,table,states,calls=self.fixture()
        request_clear(inspector,None);states[0]['maximum']=20
        confirm_clear(inspector,True,None);self.assertEqual(calls,[])
        request_clear(inspector,None);confirm_clear(inspector,True,None)
        self.assertEqual(calls,['ALL'])

    def test_full_slots_and_comp_pages(self):
        inspector,table,states,calls=self.fixture()
        states.append(self.state(id='other.speed',slot=2,comp='/other'))
        refresh(inspector,states)
        self.assertEqual(len(table.text.splitlines()),17)
        self.assertEqual(inspector.fetch('pages'),['All COMPs','/scene','/other'])
        inspector.store('selected_page','/scene');refresh(inspector,states)
        rows=table.text.splitlines()
        self.assertIn('scene.speed',rows[1])
        self.assertIn('Unassigned',rows[2]);self.assertNotIn('other.speed',table.text)

    def test_unmapped_range_and_relearn_message(self):
        inspector,table,states,calls=self.fixture()
        states[0].update(mapped=False,requires_relearn=True)
        refresh(inspector,states);row=self.row(table)
        self.assertEqual((row['Min'],row['Max'],row['Error']),('0','10','Needs re-LEARN'))

if __name__=='__main__':unittest.main()

class ContextConfirmationTests(unittest.TestCase):
    inspector=InspectorTests.inspector
    state=InspectorTests.state
    fixture=ConfirmationTests.fixture
    def test_identical_targets_in_other_track_expire_confirmation(self):
        inspector,table,states,calls=self.fixture();controller=inspector.parent()
        selected={'key':('layout','trackA','pluginA'),'label':'A'}
        controller.GetLayoutContext=lambda:dict(selected)
        request_clear(inspector,None)
        selected.update(key=('layout','trackB','pluginB'),label='B')
        self.assertFalse(confirm_clear(inspector,True,None))
        self.assertEqual(calls,[])


class OwnershipTitleTests(unittest.TestCase):
    inspector=InspectorTests.inspector
    def test_owner_recovery_changes_watched_title_even_without_targets(self):
        inspector,table=self.inspector();context=dict(key=('L','T','D'),label='Same',category='COMP',owner=dict(path='../source',state='missing'),quarantined=True)
        inspector.parent=lambda:SimpleNamespace(GetLayoutContext=lambda:context)
        refresh(inspector,[]);old=inspector.op('title').par.text
        self.assertIn('missing',old);self.assertIn('Needs Activate',old)
        context['owner']['state']='bound';refresh(inspector,[])
        self.assertNotEqual(old,inspector.op('title').par.text);self.assertIn('bound',inspector.op('title').par.text)

class RegistryMetadataTests(unittest.TestCase):
    def test_empty_inactive_owner_change_publishes_metadata_without_value_noise(self):
        import json
        inspector,table=InspectorTests().inspector();metadata=SimpleNamespace(text='');old_op=inspector.op
        inspector.op=lambda name:metadata if name=='context_state' else old_op(name)
        layouts=[dict(id='routing',name='A',category='CUSTOM'),dict(id='browsed',name='B',category='COMP',owner=dict(id='b',state='bound',path='../B'))]
        context=dict(key=('routing','T','D'),label='A',revision=1)
        inspector.parent=lambda:SimpleNamespace(GetLayoutContext=lambda:context,GetLayouts=lambda:layouts)
        refresh(inspector,[]);title=inspector.op('title').par.text;content=metadata.text
        context['revision']=123;refresh(inspector,[]);self.assertEqual(content,metadata.text)
        layouts[1]['owner']['state']='missing';refresh(inspector,[])
        self.assertNotEqual(content,metadata.text);self.assertEqual(title,inspector.op('title').par.text)
        self.assertEqual(json.loads(metadata.text)['layouts'][1]['owner']['state'],'missing')


class PulseProjectionTests(unittest.TestCase):
    def test_pulse_masks_internal_zero_without_changing_mapping_health(self):
        inspector,table=InspectorTests().inspector()
        state=InspectorTests().state(mode='pulse',value_source='pulse',value=0)
        refresh(inspector,[state]);row=InspectorTests().row(table)
        self.assertEqual(row['Value'],'Pulse');self.assertEqual(row['Mapped'],'Yes')
        self.assertEqual(state['value'],0);self.assertTrue(state['valid']);self.assertTrue(state['mapped'])


class InitializationMetadataTests(unittest.TestCase):
    def test_early_builder_refresh_does_not_initialize_missing_layout_module(self):
        inspector,table=InspectorTests().inspector();metadata=SimpleNamespace(text='');old=inspector.op
        inspector.op=lambda name:metadata if name=='context_state' else old(name)
        def not_ready():raise AssertionError('Layout DAT not installed during Inspector build')
        inspector.parent=lambda:SimpleNamespace(GetLayoutContext=lambda:dict(key=None,label='Initializing',legacy=True),GetLayouts=not_ready)
        refresh(inspector,[])
        self.assertIn('Initializing',inspector.op('title').par.text);self.assertIn('"layouts": []',metadata.text)
