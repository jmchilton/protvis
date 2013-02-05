from mz5 import Mz5

from shutil import copyfile

DO_CONVERT = False


def GetSpectrumFromScan(filename, scan_index):
    mz5_object = Mz5(filename)
    mz5_object.open()
    try:
        scan = mz5_object.get_scan(scan_index)
        ions = zip(scan.get_mzs(), scan.get_intensities())
        return {"ions": ions, "intensity": True, "pepmass": scan.get_pepmass()}
    finally:
        mz5_object.close()


def ToBinary(f, dst, name):
    copyfile(f, dst)
