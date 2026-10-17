import tests
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as S
from unittest import TestCase
from unittest.mock import Mock,patch
from test_owned_inspector import load
from test_inspector_hardware import Panel

SOURCE=Path(__file__).resolve().parents[1]
upgrade=load('mix_inspector_upgrade',SOURCE/'upgrade/upgrade_mix_inspector.py')


class Model:
    pass


class View:
    pass


class MixUpgradeTests(TestCase):
    def fixture(self):
        controller=Panel('controller');wrapper=Panel('inspector',controller)
        model=Panel('inspector_model',wrapper);model.ext=S(InspectorModel=Model())
        runtime=Panel('mix_runtime',controller,'textDAT');runtime.module=S(MixRuntime=object(),inspection=object())
        module=Panel('RotoPythonExt',controller,'textDAT');module.module=runtime.module
        for name in ('inspector_data','owned_runtime'):Panel(name,wrapper,'textDAT')
        data=Panel('live_model',model,'textDAT');data.module=S(InspectorModel=Model)
        views=[];events=[]
        for name in ('inspector_below','inspector_popup'):
            view=Panel(name,wrapper);views.append(view);view.ext=S(InspectorView=View())
            ui=Panel('ui',view,'textDAT');ui.module=S(InspectorView=View)
            for n,kind in [('text_title','textCOMP'),('text_style','textCOMP'),('container_scroll','containerCOMP'),('container_context_menu','containerCOMP')]:Panel(n,view,kind)
            for n in ('window_main','window_editor'):
                window=Panel(n,view,'windowCOMP');window.isOpen=False
        lifecycle=S(validate=Mock(return_value=(wrapper,model,views)),quiesce=Mock(side_effect=lambda c:events.append('quiesce')),initialize=Mock(side_effect=lambda c:events.append('initialize')))
        wrapper.op('owned_runtime').module=lifecycle
        wrapper.storage={'owned_inspector_sources':{'build':'old'},'user':[3,4]}
        wrapper.unstore=lambda key:wrapper.storage.pop(key,None)
        extension=S(ownerComp=controller,_process=None,_hardware_config=None,_layouts=None,_cancel_inspector_refresh=Mock(),_publish_inspector=Mock())
        controller.ext=S(RotoPythonExt=extension)
        controller.initializeExtensions=Mock(side_effect=lambda i:events.append('extension'))
        controller.Applybinding=Mock(return_value=True)
        controller.save=Mock(side_effect=lambda path:(Path(path).write_bytes(b'recovery'),events.append('recovery')))
        return controller,wrapper,model,views,events

    def test_recovery_precedes_mutation_repeat_preserves_all_nodes_and_storage(self):
        controller,wrapper,model,views,events=self.fixture()
        before={node.id for node in controller.findChildren()}
        with TemporaryDirectory() as directory,patch.object(upgrade,'project',S(folder=directory,name='expected'),create=True):
            result=upgrade.install(controller,SOURCE,expected_project=Path(directory)/'expected.toe',recovery_path=Path(directory)/'first.tox')
            self.assertEqual(events,['recovery','quiesce','extension','initialize'])
            self.assertEqual(len(result['hashes']),7)
            for path,source in result['source_paths'].items():
                node=next(node for node in controller.findChildren() if node.path==path)
                self.assertEqual(node.text,Path(source).read_text());self.assertEqual(node.par.file.eval(),'')
            first={node.id for node in controller.findChildren()}
            self.assertTrue(before<first)
            upgrade.install(controller,SOURCE,expected_project=Path(directory)/'expected.toe',recovery_path=Path(directory)/'second.tox')
            self.assertEqual({node.id for node in controller.findChildren()},first)
            self.assertEqual(wrapper.storage,{'user':[3,4]})

    def test_project_owner_transport_missing_source_or_panel_rejects_before_recovery(self):
        for fault in ('project','owner','midi','serial','source','panel','window'):
            with self.subTest(fault=fault),TemporaryDirectory() as directory:
                controller,wrapper,model,views,events=self.fixture()
                if fault=='owner':controller.ext.RotoPythonExt.ownerComp=object()
                if fault=='midi':controller.ext.RotoPythonExt._process=object()
                if fault=='serial':controller.ext.RotoPythonExt._hardware_config=S(active=True)
                if fault=='source':controller.op('mix_runtime').OPType='tableDAT'
                if fault=='panel':views[1].op('container_scroll').OPType='textCOMP'
                if fault=='window':views[1].op('window_editor').OPType='containerCOMP'
                with patch.object(upgrade,'project',S(folder=directory,name='expected'),create=True):
                    with self.assertRaises(ValueError):
                        upgrade.install(controller,SOURCE,expected_project=Path(directory)/('wrong.toe' if fault=='project' else 'expected.toe'),recovery_path=Path(directory)/'recovery.tox')
                controller.save.assert_not_called();self.assertEqual(events,[])

    def test_existing_or_failed_recovery_stops_before_source_and_widget_changes(self):
        for fault in ('existing','empty'):
            with self.subTest(fault=fault),TemporaryDirectory() as directory:
                controller,wrapper,model,views,events=self.fixture()
                before={node.id for node in controller.findChildren()}
                recovery=Path(directory)/'recovery.tox'
                if fault=='existing':recovery.write_bytes(b'earlier')
                else:controller.save.side_effect=lambda path:Path(path).write_bytes(b'')
                with patch.object(upgrade,'project',S(folder=directory,name='expected'),create=True):
                    with self.assertRaises((ValueError,RuntimeError)):
                        upgrade.install(controller,SOURCE,expected_project=Path(directory)/'expected.toe',recovery_path=recovery)
                self.assertEqual({node.id for node in controller.findChildren()},before)
                wrapper.op('owned_runtime').module.quiesce.assert_not_called()
                controller.initializeExtensions.assert_not_called()
