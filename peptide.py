from parameters import UNIMOD_FILE
from pyteomics.mass import Unimod
import re

UNIMOD = Unimod(url="file://%s" % UNIMOD_FILE)


def read_peptide_info(peptide_string,
                      protein="Input",
                      sort="peptide",
                      expect=-1.0,
                      masstol=0):
    """
    Tries to part out protvis required peptide information
    from a flexible string representation.

    >>> info = read_peptide_info("ABCDE")
    >>> info["peptide"]
    'ABCDE'
    >>> info = read_peptide_info("ABCDE;144.102063@N-term")
    >>> mod_info = info["modification_info"]
    >>> mod_info[0]["mod_nterm_mass"]
    144.102063
    >>> info = read_peptide_info("ABCDE;iTRAQ4plex@N-term")
    >>> mod_info = info["modification_info"]
    >>> mod_info[0]["mod_nterm_mass"]
    144.102063
    >>> info = read_peptide_info("ABCDE;iTRAQ4plex@1")
    >>> mod_info = info["modification_info"]
    >>> mod_info[0]["mod_aminoacid_mass"][0]
    1
    >>> mod_info[0]["mod_aminoacid_mass"][1]
    144.102063
    >>> info = read_peptide_info("ABCDE; iTRAQ4plex (A) @1")
    >>> mod_info = info["modification_info"]
    >>> mod_info[0]["mod_aminoacid_mass"][0]
    1
    >>> mod_info[0]["mod_aminoacid_mass"][1]
    144.102063
    """
    peptide_parts = [part.strip() for part in peptide_string.split(";")]
    peptide_sequence = peptide_parts[0]
    peptide_mod_strings = peptide_parts[1:]
    mods = []
    for peptide_mod_string in peptide_mod_strings:
        (mod, site) = peptide_mod_string.rsplit("@", 1)
        if not mod or not site:
            continue
        mod = mod.strip()
        site = site.strip()
        try:
            mass = float(mod)
        except ValueError:
            unimod_entry = _find_unimod_entry(mod)
            if not unimod_entry:
                continue
            mass = float(unimod_entry["mono_mass"])
        if site.isdigit():  # single amino acid
            mods.append({"mod_aminoacid_mass": (int(site), mass)})
        elif site.lower()[0] == "n":
            mods.append({"mod_nterm_mass": mass})
        elif site.lower()[0] == "c":
            mods.append({"mod_cterm_mass": mass})
    return {"peptide": peptide_sequence,
            "modification_info": mods or None,
            "protein": protein,
            "sort": sort,
            "expect": expect,
            "masstol": masstol}


def _find_unimod_entry(label):
    entry = _find_unimod_entry_exact(label)
    if entry:
        return entry

    # No an exact entry, maybe contains amino acid listed at the end
    entryWithAAMatch = re.match(r'^(.*) \([a-zA-Z]\)$', label)
    if entryWithAAMatch:
        possibleName = entryWithAAMatch.group(1)
        entry = _find_unimod_entry_exact(possibleName)
        if entry:
            return entry

    return None


def _find_unimod_entry_exact(label):
    entry = UNIMOD.by_title(label)
    if entry:
        return entry

    entry = UNIMOD.by_name(label)
    if entry:
        return entry

    return None
