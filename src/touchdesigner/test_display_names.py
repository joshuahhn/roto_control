"""Display edits preserve the acknowledged session and stable identities."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).parent / 'code/py/roto_python'))
from protocol import Host, digest, sysex, text13
from collection_protocol import CollectionHost

class DisplayNamesTests(unittest.TestCase):
    def test_refresh_is_metadata_only_and_preserves_mapping(self):
        sent=[]
        host=Host(sent.append, lambda value: None)
        host.connected=host.plugin=host.mapped=True
        identity=host.device_id
        host.set_display_names('LIVE FX','VISUAL')
        self.assertEqual(sent, [sysex(10,0x16,text13('LIVE FX')),
            sysex(11,5,(0,*digest(identity,8),1,*text13('VISUAL'),0,0)),sysex(11,6)])
        self.assertEqual(host.device_id, identity)
        self.assertTrue(host.mapped)
        self.assertFalse(host.set_display_names('LIVE FX','VISUAL'))
        self.assertEqual(len(sent),3)

    def test_validation_and_learn_are_atomic(self):
        host=Host(lambda message: self.fail('must not send'),lambda value:None)
        for track,plugin in [('1234567890123','CUSTOM'),('EFFECT','中文'),('EFFECT','bad\x00')]:
            with self.assertRaises(ValueError): host.set_display_names(track,plugin)
            self.assertEqual((host.track_name,host.plugin_name),('EFFECT','CUSTOM'))
        host.learning=True
        with self.assertRaises(ValueError): host.set_display_names('NEW','NAME')
        self.assertEqual((host.track_name,host.plugin_name),('EFFECT','CUSTOM'))

    def test_collection_default_names_and_hash_independence(self):
        sent=[]
        host=CollectionHost(sent.append,lambda *args:None,[], 'stable',allow_empty=True)
        host._devices()
        first=sent[2]
        host.set_display_names('EFFECT','OTHER')
        sent.clear(); host._devices()
        self.assertEqual(first[8:16],sent[2][8:16])
        self.assertEqual(bytes(sent[2][17:30]).rstrip(b'\0'),b'OTHER')
        self.assertEqual(sent[-1],sysex(11,8,(0,0,0)))
