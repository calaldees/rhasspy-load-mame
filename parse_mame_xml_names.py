import os
import re
import pathlib

import xml.etree.ElementTree as ET
from zipfile import ZipFile


PATH_OUTPUT = 'rhasspy'


def _zip_filehandle(filename):
    zipfile = ZipFile(filename)
    _filename = zipfile.namelist()[0]
    filehandle = zipfile.open(_filename)
    return filehandle

def _zip_filehandles(zip_filename, files=frozenset()):
    with ZipFile(zip_filename) as zipfile:
        for _filename in zipfile.namelist():
            if _filename.endswith('.xml') and (not files or _filename in files):
                with zipfile.open(_filename) as filehandle:
                    yield filehandle #from iter_software(lambda: filehandle)

def _tag_iterator(iterparse, tag):
    for _, e in iterparse:
        if e.tag == tag:
            yield e

def _find_recursively(element, func_select):
    for child in element:
        if func_select(child):
            yield child
        else:
            yield from _find_recursively(child, func_select)


EXCLUDE_SOURCEFILE = {
    # Console multisystems
    'nss.cpp',
    'playch10.cpp',
    'vsnes.cpp',
    'megaplay.cpp',
    'megatech.cpp',

    # Casino games???
    'peplus.cpp',
    'aristmk6.cpp',
    'bfm_sc4.cpp',
    'nbmj8891.cpp',
    'statriv2.cpp',
    'att3b2.cpp',
    'ecoinf2.cpp',
    'highvdeo.cpp',
    'mpu4vid.cpp',
    'norautp.cpp',

    #other?
    'decocass.cpp',
    'spg2xx_jakks.cpp',  # TV game?
    'hh_hmcs40.cpp',  # LCD Donkey kong? coleco?
}
def iter_mame_names(get_xml_filehandle):
    r"""
    >>> data = '''<?xml version="1.0"?>
    ... <mame build="0.222 (unknown)" debug="no" mameconfig="10">
    ...     <machine name="18wheelr" sourcefile="naomi.cpp" romof="naomi">
    ...         <description>18 Wheeler (deluxe, Rev A)</description>
    ...     </machine>
    ...     <machine name="18wheelro" sourcefile="naomi.cpp" cloneof="18wheelr" romof="18wheelr">
    ...         <description>18 Wheeler (deluxe)</description>
    ...     </machine>
    ...     <machine name="naomi" sourcefile="naomi.cpp" isbios="yes">
    ...         <description>Naomi BIOS</description>
    ...     </machine>
    ...     <machine name="peip0028" sourcefile="peplus.cpp">
    ...         <description>Player's Edge Plus (IP0028) Joker Poker - French</description>
    ...     </machine>
    ...     <machine name="machine" sourcefile="machine.cpp">
    ...         <softwarelist tag="pc_disk_list" name="ibm5150" status="original"/>
    ...     </machine>
    ... </mame>'''.encode('utf8')
    >>> from unittest.mock import MagicMock
    >>> mock_filehandle = MagicMock()
    >>> mock_filehandle.return_value.read.side_effect = (data, b'')
    >>> tuple(iter_mame_names(mock_filehandle))
    (('18wheelr', '18 Wheeler (deluxe, Rev A)'),)
    """
    assert callable(get_xml_filehandle)
    for machine in _tag_iterator(ET.iterparse(get_xml_filehandle()), 'machine'):
        if machine.get('cloneof') or \
            machine.get('isbios') == 'yes' or \
            machine.get('isdevice') == "yes" or \
            machine.get('runnable') == "no" or \
            machine.get('ismechanical') == "yes" or \
            machine.get('sourcefile') in EXCLUDE_SOURCEFILE or \
            isinstance(machine.find('softwarelist'), ET.Element)\
        :
            continue
        yield (
            machine.get('name'),
            machine.find('description').text,
        )

#def iter_software_names(get_xml_filehandle):
def iter_software_names(filehandle):
    r"""
    >>> data = '''<?xml version="1.0"?>
    ... <softwarelists>
    ...     <softwarelist name="sms" description="Sega Master System cartridges">
    ...         <software name="alexkidd">
    ...                 <description>Alex Kidd in Miracle World (Euro, USA, v1)</description>
    ...                 <part name="cart" interface="sms_cart">
    ...                         <dataarea name="rom">
    ...                             <rom name="alex kidd in miracle world (usa, europe) (v1.1).bin" sha1="6d052e0cca3f2712434efd856f733c03011be41c"/>
    ...                             <rom name="some other rom.bin" sha1="xxx"/>
    ...                         </dataarea>
    ...                 </part>
    ...         </software>
    ...         <software name="alexkidd1" cloneof="alexkidd">
    ...                 <description>Alex Kidd in Miracle World (Euro, USA, v0)</description>
    ...                 <part name="cart" interface="sms_cart">
    ...                         <dataarea name="rom">
    ...                             <rom name="alex kidd in miracle world (usa, europe).bin" sha1="8cecf8ed0f765163b2657be1b0a3ce2a9cb767f4"/>
    ...                             <rom test="no name in field list" />
    ...                         </dataarea>
    ...                 </part>
    ...         </software>
    ...     </softwarelist>
    ... </softwarelists>'''.encode('utf8')
    >>> from unittest.mock import MagicMock
    >>> mock_filehandle = MagicMock()

    #>>> mock_filehandle.return_value.read.side_effect = (data, b'')
    >>> mock_filehandle.read.side_effect = (data, b'')

    >>> tuple(iter_software_names(mock_filehandle))
    (('Alex Kidd in Miracle World (Euro, USA, v1)', 'sms/alexkidd'),)
    """
    #callable(get_xml_filehandle)
    #iterparse = ET.iterparse(source=get_xml_filehandle(), events=('start', 'end'))
    iterparse = ET.iterparse(source=filehandle, events=('start', 'end'))
    current_softwarelist = ''
    for event, e in iterparse:
        if event == 'start' and e.tag == 'softwarelist':
            current_softwarelist = e.get('name')
        if event == 'end' and e.tag == 'software':
            #for rom in _find_recursively(e, lambda e: e.tag == 'rom'):
            #    if not rom.get('name'):
            #        # log.warning(f"software {e.get('name')} has a rom with no name?")
            #        continue
            if e.get('cloneof'):  # no clone support for now
                continue
            yield (
                #rom.get('name'),
                e.find('description').text,
                os.path.join(current_softwarelist, e.get('name')),
            )



EXCLUDE_STR ={
    '(handheld',
    'mahjong',
    'casino',
    'jackpot',
    'print club',
    'poker',
    'bingo',
}
def normalise_name(name):
    """
    >>> _n = normalise_name

    # UNEEDED? We don't use ROM names
    #>>> _n('alex kidd in miracle world (usa, europe) (v1.1).bin')
    #'alex kidd in miracle world'
    #>>> _n('animatix (infogrames) (j. pages, c. belin) (1985) (mo6 k7).k7')
    #'animatix'
    >>> _n('Alex Kidd in Miracle World (Euro, USA, v1)')
    'alex kidd in miracle world'

    >>> _n('18 Wheeler (deluxe, Rev A)')
    '18 wheeler'
    >>> _n('Yam! Yam!?')
    'yam yam'
    >>> _n('X-Men: Children of the Atom (Euro 950331)')
    'x men children of the atom'
    >>> _n('X-Men Vs. Street Fighter (Euro 961004)')
    'x men versus street fighter'
    >>> _n('Vampire Savior 2: The Lord of Vampire (Japan 970913)')
    'vampire savior 2 the lord of vampire'
    >>> _n('U.S. Classic')
    'u s classic'
    >>> _n('Venom & Spider-Man - Separation Anxiety (SNES bootleg)')
    'venom and spider man separation anxiety'
    >>> _n('Vindicators Part II')
    'vindicators part two'
    >>> _n('World Rally 2: Twin Racing')
    'world rally 2 twin racing'
    >>> _n('Wonder Boy III - Monster Lair (set 6, World, System 16B) (8751 317-0098)')
    'wonder boy three monster lair'
    >>> _n('Touch & Go')
    'touch and go'
    >>> _n('Double Dragon (Neo-Geo)')
    'double dragon neo geo'
    >>> _n('Robocop 2 (handheld)')
    >>> _n("Player's Edge Plus (IP0028) Joker Poker - French")

    Broken names with multiple titles - TODO
    >>> _n('Virtua Tennis 2 / Power Smash 2 (Rev A) (GDS-0015A)')
    'virtua tennis 2 power smash 2'
    >>> _n('Xtreme Rally / Off Beat Racer!')
    'xtreme rally off beat racer'

    """
    name = name.lower()
    for exclude_str in EXCLUDE_STR:
        if exclude_str in name:
            return None
    #name = re.sub(r"(\..{1,4})$", '', name)  # Remove file extension
    name = re.sub(r"'", '', name)  # remove single quotes
    name = re.sub(r"\(neo[ -_]?geo.*\)", 'neo geo', name, flags=re.IGNORECASE)  # preserve neo geo in name
    name = re.sub(r'\(.*\)', '', name)  # remove items in parenthesis
    name = re.sub(r'&', 'and', name)  # replace & with and
    name = re.sub(r'\W', ' ', name)  # remove all non-alpha-numeric characters
    name = re.sub(r' +', ' ', name)  # compact multiple spaces down to a single space
    name = re.sub(r' iii', ' three', name)  # replace roman numerals (CRUDE)
    name = re.sub(r' ii', ' two', name)
    name = re.sub(r' vs ', ' versus ', name)  # replace pronunciation of versus
    name = name.strip()
    return name


def mame_names():
    output_filename = os.path.join(PATH_OUTPUT, 'mame')
    with open(output_filename, 'wt') as output_filehandle:
        for rom, name in iter_mame_names(lambda: _zip_filehandle('mamelx.zip')):
            name = normalise_name(name)
            if not name:
                continue
            output_filehandle.write(f'({name}):{rom}\n')
            #print(f'({name}):{rom}')


SYSTEMS = {
    'sms',
    'megadriv',
    'nes',
    'snes',
    'tg16',
    'pce',
    'a2600',
    '32x',
    'neogeo',
}
def software_list_names():
    for filehandle in _zip_filehandles('hash.zip'):
        system_name = pathlib.Path(filehandle.name).stem
        if system_name not in SYSTEMS:
            continue
        output_filename = os.path.join(PATH_OUTPUT, system_name)
        with open(output_filename, 'wt') as output_filehandle:
            for name, archive_filename in iter_software_names(filehandle):
                name = normalise_name(name)
                if not name:
                    continue
                output_filehandle.write(
                    f'({name}):{archive_filename}\n'
                )
                #print()


if __name__ == "__main__":
    #postmortem(main)
    os.makedirs(PATH_OUTPUT, exist_ok=True)
    mame_names()
    software_list_names()