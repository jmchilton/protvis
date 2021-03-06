from unittest import TestCase

from protvis.conversion import _ready_source_file
from protvis.FileTypes import MGF
from protvis.FileTypes import MzML
from os.path import basename
from os import remove


KEEP_OUTPUT = True


class ParserTest(TestCase):

    def _test_module(self, module, source):
        dest = 'dest_%s' % basename(source)
        try:
            (src, close) = _ready_source_file(source, dest, module)
            name = 'moocow'
            module.ToBinary(src, dest, name)
            spectrum_info = module.GetSpectrumFromScan(dest, 1)
            ions = spectrum_info['ions']
            self.assertAlmostEqual(112.0870743, ions[0][0], 4)
            self.assertAlmostEqual(3164.949463, ions[0][1], 4)
            self.assertEquals(len(ions), 239)
            self.assertTrue(spectrum_info['intensity'])
            self.assertAlmostEqual(367.201873, spectrum_info['pepmass'], 4)
            #print spectrum_info
        finally:
            if not KEEP_OUTPUT:
                remove(dest)

    def test_mzml(self):
        self._test_module(MzML, 'test_data/test.mzML')

    def test_mgf(self):
        source = 'test_data/test.mgf'
        dest = 'dest_%s' % basename(source)
        try:
            (src, close) = _ready_source_file(source, dest, MGF)
            name = 'moocow'
            MGF.ToBinary(src, dest, name)
            offset = MGF.GetOffsetFromSpectrum(dest, "test.2.2.2")
            assert offset > 0
        finally:
            if not KEEP_OUTPUT:
                remove(dest)
