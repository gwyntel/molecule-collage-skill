"""Offline regression checks: complete files, transparency, layout and recovery."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from molecule_collage import render, resolve, validate_image

EXAMPLE = Path(__file__).resolve().parents[1]/'assets/example.json'

class CollageTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(EXAMPLE.read_text())
        self.config.update(width=800,height=1000)
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def test_photo_fill_and_complete_outputs(self):
        photo = self.root/'source.png'
        Image.new('RGB',(250,300),(190,40,100)).save(photo)
        checks = render(self.config,photo,self.root/'art')
        self.assertEqual(checks['collage.png']['height'],1000)
        with Image.open(self.root/'art/overlay.png') as im:
            im.load()
            self.assertEqual(im.getchannel('A').getextrema(),(0,255))
        self.assertTrue((self.root/'art/validation.json').exists())
        with self.assertRaises(FileExistsError):
            render(self.config,photo,self.root/'art')
    def test_truncated_image_rejected(self):
        render(self.config,None,self.root/'art')
        payload = (self.root/'art/collage.png').read_bytes()
        broken = self.root/'broken.png'
        broken.write_bytes(payload[:len(payload)//2])
        with self.assertRaises((OSError,SyntaxError)):
            validate_image(broken)
    def test_layout_overlap_rejected(self):
        for item in self.config['compounds']:
            item['box'] = [0,0,300,300]
        with self.assertRaisesRegex(ValueError,'overlap'):
            render(self.config,None,self.root/'bad')
        self.assertFalse((self.root/'bad').exists())
    def test_label_free_custom_layout_and_outline(self):
        self.config.update(labels=False,mode='outline')
        for item,box in zip(self.config['compounds'],[[10,10,380,400],[410,10,380,400],[410,600,380,390]]):
            item['box']=box
        render(self.config,None,self.root/'custom')
        self.assertTrue(validate_image(self.root/'custom/mask.png')['full_decode'])
    def test_invalid_or_unresolved_identity(self):
        for smiles in ['invalid SMILES','']:
            config=copy.deepcopy(self.config)
            config['compounds'][0]['smiles']=smiles
            with self.assertRaises(ValueError): resolve(config)
    def test_stereochemistry_retained(self):
        config={'compounds':[{'name':'specified stereoisomer','smiles':'N[C@@H](C)C(=O)O'}]}
        result=resolve(config)
        self.assertIn('@',result['compounds'][0]['smiles'])

if __name__=='__main__': unittest.main()
