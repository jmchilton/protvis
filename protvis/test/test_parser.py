from unittest import TestCase
import os
from protvis.FileTypes import MzML, MZ5
from protvis.conversion import _ready_source_file

KEEP_OUTPUT = True


class ParserTest(TestCase):

    def _test_module(self, module, source):
        dest = 'dest_%s' % os.path.basename(source)
        try:
            (src, close) = _ready_source_file(source, dest, module)
            name = 'moocow'
            module.ToBinary(src, dest, name)
            #if module == MzML:
            #    spectrum_info = module.GetSpectrumFromScan(dest, 3)
            #    ions = spectrum_info['ions']
            #    self.assertAlmostEqual(112.0870438, ions[0][0], 4)
            #    self.assertAlmostEqual(1499.820923, ions[0][1], 4)

            #spectrum = MzML.Display('test123', None)
            #{'ions': [[0.3287000060081482, 16.638999938964844], [360.0130310058594, 1799.3558349609375], [7.334797566185768e+28, 4.8553738361977516e+33], [1.6815581571897805e-44, 3.0290467604845246e-41], [3.3491033297363128e-43, 1.401298464324817e-45], [1.401298464324817e-45, 0.8156999945640564], [367.2018737792969, 112.08707427978516], [3164.949462890625, 112.09429168701172], [334.75555419921875, 113.07115936279297], [758.64599609375, 113.09236145019531], [263.3543395996094, 113.10687255859375], [228.20021057128906, 114.09683227539062], [392.9256591796875, 114.1108169555664], [22860.2265625, 115.0865478515625], [2473.555908203125, 115.10787200927734], [22343.251953125, 115.13238525390625], [113.0778579711914, 116.07074737548828], [3558.239990234375, 116.09823608398438], [3473.081787109375, 116.11115264892578], [26577.806640625, 116.12602233886719], [100.75849151611328, 116.12887573242188], [131.96728515625, 116.13278198242188], [100.32669067382812, 116.13615417480469], [122.94659423828125, 117.07418060302734], [172.19033813476562, 117.07769012451172], [78.43367004394531, 117.11449432373047], [22765.3046875, 117.12846374511719], [134.4080047607422, 117.1319808959961], [164.1682891845703, 118.1176528930664], [449.0561218261719, 127.05030822753906], [119.546630859375, 127.08676147460938], [260.07269287109375, 129.11361694335938], [150.20558166503906, 130.09754943847656], [529.136474609375, 140.08224487304688], [148.8434295654297, 141.06619262695312], [167.5823211669922, 143.109619140625], [163.6455535888672, 145.06190490722656], [239.2296142578125, 145.10787963867188], [3665.340087890625, 146.11044311523438], [158.7482452392578, 147.03329467773438], [371.4373474121094, 152.08152770996094], [178.67286682128906, 153.05044555664062], [483.988525390625, 154.09742736816406], [152.6966552734375, 155.04286193847656]], 'intensity': True, 'pepmass': 100.8104019165039, 'charge': 0, 'offset': 0}
            if module == MzML:
                spectrum_info = module.GetSpectrumFromScan(dest, 1)
            else:
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
                os.remove(dest)

    def test_mzml(self):
        self._test_module(MzML, 'test_data/test.mzML')

    def test_mz5(self):
        self._test_module(MZ5, 'test_data/test.mz5')
