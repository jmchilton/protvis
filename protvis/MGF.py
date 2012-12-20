from Common import *

class Result:
    def __init__(self, title, offset):
        self.HitInfo = { "spectrum": title, "offset": offset }

class Parameter:
    def __init__(self, name, value, index):
        self.name = name
        self.value = value
        self.index = index

    def __str__(self):
        if self.index != None:
            return self.name + "[" + str(self.index) + "]=" + self.value
        return self.name + "=" + self.value

    @staticmethod
    def TryParse(line):
        idx = line.find("=")
        if idx > 0:
            var = line[:idx].rstrip()
            val = line[idx + 1:].lstrip()
            idx = var.find("[")
            arr = None
            if idx >= 0:
                arr = int(var[idx + 1:-1].strip())
                var = var[:idx].rstrip()
            return Parameter(var, val, arr)
        return None

class Spectrum:
    """
    struct Ion {
            float mass;
            float intensity;
    }
    struct Spectrum {
            BYTE OptionalFlags;
            DWORD ions__count;
            float pepmass; //ONLY IF (OptionalFlags & 0x01)
            Ion ions[ions__count];
    }
    """
    def __init__(self, f):
        self.stream = f
        #self.params = []
        self.ions = []
        self.title = None

    def end(self):
        pepmass = None
        intensity = TryGet(TryGet(self.ions, 0), 1)
        #for p in self.params:
        #       if p.name == "PEPMASS":
        #               pepmass = float(p.value.split(" ")[0])
        #       elif p.name == "TITLE":
        #               self.title = p.value
        self.stream.write(struct.pack("=BI", EncodeOptional(pepmass, intensity), len(self.ions)))
        if pepmass:
            self.stream.write(struct.pack("=f", pepmass))
        if intensity:
            for i in self.ions:
                self.stream.write(struct.pack("=ff", i[0], i[1]))
        else:
            for i in self.ions:
                self.stream.write(struct.pack("=f", i[0]))

    def parameter(self, param):
        #self.params.append(param)
        if param.name == "PEPMASS":
            pepmass = float(param.value.split(" ")[0])
        elif param.name == "TITLE":
            self.title = param.value

    def ion(self, mass, intensity):
        self.ions.append([mass, intensity])

    @staticmethod
    def get_info(f):
        info = {}
        [optional, count] = struct.unpack("=BI", f.read(1 + 4))
        if optional & 0x01:
            info["pepmass"] = struct.unpack("=f", f.read(4))
        else:
            info["pepmass"] = None
        if optional & 0x02:
            info["intensity"] = True
            info["ions"] = [list(struct.unpack("=ff", f.read(4 + 4))) for i in xrange(count)]
        else:
            info["intensity"] = False
            info["ions"] = [struct.unpack("=f", f.read(4))[0] for i in xrange(count)]
        return info

class Header:
    """
    struct Index {
            DWORD scan;
            DWORD charge;
            DWORD offset;
    }
    struct Header {
            DWORD spectrums__count;
            DWORD index__offset;
            String spectrum_name;
            Spectrum spectrums[spectrums__count];
            Index spectrum_index[spectrums__count];
    }
    """
    def __init__(self, f):
        self.stream = f
        self.startpos = f.tell()
        self.params = []
        self.spectrums = []
        self.spec_offset = 0
        f.write(struct.pack("=II", 0, 0))

    def end(self):
        endpos = self.stream.tell()
        self.stream.seek(self.startpos)
        self.stream.write(struct.pack("=II", len(self.spectrums), endpos))
        self.stream.seek(endpos)
        for spec in self.spectrums:
            self.stream.write(struct.pack("=III", spec[0], spec[1], spec[2]))

    def parameter(self, param):
        self.params.append(param)

    def begin_spectrum(self):
        self.spec_offset = self.stream.tell()

    def end_spectrum(self, spectrum):
        spec = spectrum.title.split(".")
        if len(self.spectrums) == 0:
            EncodeStringToFile(self.stream, ".".join(spec[:-3]))
        self.spectrums.append([int(spec[-3]), int(spec[-1]), self.spec_offset])

    @staticmethod
    def get_spectrum(f, name):
        [count, offset] = struct.unpack("=II", f.read(4 + 4))
        f.seek(offset)
        i = 0
        name = name.split(".")
        if DecodeStringFromFile(f) == ".".join(name[:-3]):
            scan = int(name[-3])
            #ignore the chage, it isn't always correct
            while i < count:
                if struct.unpack("=I", f.read(4))[0] == scan:
                    [charge, offset] = struct.unpack("=II", f.read(4 + 4))
                    f.seek(offset)
                    info = Spectrum.get_info(f)
                    info["title"] = name
                    info["charge"] = charge
                    info["offset"] = offset
                    return info
                else:
                    f.seek(4 + 4, 1)
                i += 1
        return None

    @staticmethod
    def get_spectrum_offset(f, name, force):
        [count, offset] = struct.unpack("=II", f.read(4 + 4))
        name = name.split(".")
        match = False
        if force:
            match = True
            EatStringFromFile(f)
        elif DecodeStringFromFile(f) == ".".join(name[:-3]):
            match = True
        if match:
            f.seek(offset)
            i = 0
            scan = int(name[-3])
            while i < count:
                if struct.unpack("=I", f.read(4))[0] == scan:
                    return struct.unpack("=II", f.read(4 + 4))[1]
                else:
                    f.seek(4 + 4, 1)
                i += 1
        return -1

    @staticmethod
    def search_spectrums(f, stat):
        [count, offset] = struct.unpack("=II", f.read(4 + 4))
        stat.Total = count
        spectrum = DecodeStringFromFile(f)
        f.seek(offset)
        i = 0
        while i < count:
            s = stat.copy()
            [scan, charge, offset] = struct.unpack("=III", f.read(4 + 4 + 4))
            title = spectrum + "." + str(scan) + "." + str(scan) + "." + str(charge)
            s.SearchItemString("title", title)
            if s.IsMatched():
                stat.Results.append(Result(title, offset))
            i += 1

def ToBinary(f, dst, name):
    import Reference
    dest = open(dst, "w")
    header = Header(dest)
    spectrum = None
    while True:
        line = f.readline().strip()
        if len(line) == 0:
            break
        param = Parameter.TryParse(line)
        if param:
            if spectrum:
                spectrum.parameter(param)
            else:
                header.parameter(param)
        elif spectrum != None:
            if line.upper()[:3] == "END" and line[3:].lstrip() == "IONS":
                header.end_spectrum(spectrum)
                spectrum.end()
                spectrum = None
            else:
                ion = line.split(" ")
                if len(ion) > 1:
                    spectrum.ion(float(ion[0]), float(ion[1]))
                else:
                    spectrum.ion(ion[0], None)
        elif line[:5].upper() == "BEGIN" and line[5:].lstrip() == "IONS":
            spectrum = Spectrum(dest)
            header.begin_spectrum()
        else:
            raise ValueError(line)
    header.end()
    dest.close()
    return Reference.FileType.MGF

def GetSpectrum(filename, spectrum):
    f = open(filename, "r")
    spec = Header.get_spectrum(f, spectrum)
    f.close()
    return spec

def GetSpectrumFromOffset(filename, offset):
    f = open(filename, "r")
    f.seek(offset)
    spec = Spectrum.get_info(f)
    f.close()
    return spec

def GetOffsetFromSpectrum(filename, spectrum, force = False):
    f = open(filename, "r")
    offset = Header.get_spectrum_offset(f, spectrum, force)
    f.close()
    return offset

def Search(filename, terms):
    f = open(filename, "r")
    stat = SearchStatus(terms)
    Header.search_spectrums(f, stat)
    f.close()
    return [0, stat.Total, stat.Results]

def DefaultSortColumn(scores):
    return ["spectrum", "Spectrum", []]
