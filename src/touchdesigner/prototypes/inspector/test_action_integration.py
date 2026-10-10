"""Shared named-action projection and freshness; no TD/native/physical claims."""
from copy import deepcopy
from unittest import TestCase
from live_model import ControllerCatalog, project_records
from parity import detail_groups, filter_choices, visible_slots
from test_live_model import Adapter, KEY
from test_activation import OTHER
import test_ownership_integration


def action(**changes):
    return dict(dict(id='mapping', kind='button', slot=1, label='Clean', comp='', parameter='',
                     minimum=0, maximum=1, value=0, value_source='action', valid=True,
                     mapped=True, connected=True, plugin=True, mode='pulse', button_type='push',
                     binding_type='action', action_id='preset.clean', action_available=True,
                     action_result=None, error=''), **changes)


class ActionIntegrationTests(TestCase):
    def model(self, record=None):
        a=Adapter(); a.records[KEY]=[record or action()]
        m=ControllerCatalog(a); m.GetCatalog(KEY)
        return a,m

    def test_action_id_result_and_failure_details_are_visible_without_value_writes(self):
        a,m=self.model()
        self.assertEqual(m.GetCatalog(KEY)[8]['Destination'], 'Action preset: preset.clean')
        self.assertEqual(m.ValueText(KEY,8), 'Ready')
        for result in (dict(status='succeeded',error=''),dict(status='partial',error='changed target',entries=[dict(actual_value=.6)])):
            a.records[KEY][0].update(action_result=deepcopy(result),error=result['error'])
            m.Sync()
            self.assertEqual(m.ValueText(KEY,8), result['status'])
            self.assertEqual(m.Info(KEY,8)['action_result'],result)
            health=m.Health(KEY,8)
            if result['status']=='partial':self.assertEqual(health['code'],'action_failed')
            groups=detail_groups(m.Info(KEY,8),health,m.Status,None,KEY,KEY,('track','device'),True)
            self.assertIn('preset.clean',str(groups))
            self.assertIn(result['status'] if not result['error'] else result['error'],str(groups))
            self.assertLessEqual(len(groups[0][1]),3)  # existing compact row pool
        self.assertEqual(a.writes,[])
        self.assertEqual(m.MappingSchema(KEY,8)['modes'],('pulse',))
        self.assertFalse(m.Capabilities(KEY,8)['value']['enabled'])

    def test_provider_result_notification_does_not_expire_assignment_token(self):
        a,m=self.model(action(action_result=dict(status='succeeded',entries=[dict(actual_value=.5)])))
        token=m.GetToken(KEY,8); events=[]
        m.Subscribe('view',KEY,lambda *args:events.append(args))
        a.records[KEY][0]['action_result']['entries'][0]['actual_value']=.6
        m.Sync();m.Flush()
        self.assertEqual(m.GetToken(KEY,8),token)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0][1],1<<8);self.assertEqual(events[0][2],0)
        a.records[KEY][0]['action_id']='preset.other';m.Sync()
        self.assertNotEqual(m.GetToken(KEY,8),token)

    def test_unavailable_or_quarantine_never_shows_prior_success_as_current(self):
        for fields in (dict(valid=False,action_available=False,error='Action unavailable'),
                       dict(valid=False,value_source='unavailable',error='Activate repaired Layout')):
            a,m=self.model(action(action_result=dict(status='succeeded'),**fields))
            self.assertEqual(m.ValueText(KEY,8),'Unavailable')
            self.assertEqual(m.Health(KEY,8)['code'],'invalid')

    def test_filters_and_inactive_library_preserve_action_identity_and_unavailable(self):
        source=action(value=None)
        a=test_ownership_integration.LibraryTests().adapter([], [source])
        row=a.Read(OTHER)
        self.assertEqual(row[0]['binding_type'],'action')
        self.assertTrue(row[0]['action_available'])
        rows,infos=project_records(row)
        self.assertEqual(rows[8]['Destination'],'Action preset: preset.clean')
        self.assertIn(('actions','Action presets'),filter_choices(infos))
        self.assertEqual(visible_slots(infos,'actions'),(8,))
        adapter,m=self.model(action(valid=False, action_available=False,error='Action unavailable: preset.clean'))
        self.assertEqual(m.ValueText(KEY,8),'Unavailable')
        self.assertEqual(m.Health(KEY,8)['code'],'invalid')
        self.assertIn('unavailable',m.Health(KEY,8)['detail'])
        self.assertEqual(adapter.writes,[])
