import os
import re
import pathlib
from collections import defaultdict

import xml.etree.ElementTree as ET
from zipfile import ZipFile


PATH_OUTPUT = 'slots/mame'


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
    ...     <machine name="sfa3b" sourcefile="cps2.cpp" cloneof="sfa3" romof="sfa3">.
    ...         <description>Street Fighter Alpha 3 (Brazil 980629)</description>.
    ...     </machine>
    ... </mame>'''.encode('utf8')
    >>> from unittest.mock import MagicMock
    >>> mock_filehandle = MagicMock()
    >>> mock_filehandle.return_value.read.side_effect = (data, b'')
    >>> tuple(iter_mame_names(mock_filehandle))
    (('18 Wheeler (deluxe, Rev A)', '18wheelr'),)
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
            machine.find('description').text,
            machine.get('name'),
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


"""
<softwarelist name="vgmplay" description="Video Game Music Files">
    <software name="lemmings_pc">
        <description>Lemmings DOS</description>
        <part name="001" interface="vgm_quik">
                <feature name="part_id" value="00_lets_go.vgm" />
        </part>
    </software>
    <software name="lemmings_nes">
        <description>Lemmings (NES)</description>
        <part name="001" interface="vgm_quik">
                <feature name="part_id" value="01 title screen.vgz" />
        </part>
    </software>
    <software name="lemmings_zxs">
            <description>Lemmings (ZX Spectrum 128)</description>
    </software>
    <software name="lemmings_t1k">
            <description>Lemmings Series (Tandy 1000)</description>
    </software>
    <software name="lemmings">
            <description>Lemmings (Arcade)</description>
    </softare>
    <software name="lemmings_md">
            <description>Lemmings (GEN/MD)</description>
    </softare>
    <software name="lemmings_sms">
            <description>Lemmings (SMS)</description>
    </software>
</softwarelists>
"""


EXCLUDE_STR ={
    '(handheld',
    'mahjong',
    'casino',
    'jackpot',
    'print club',
    'poker',
    'bingo',
}
def normalise_name(name: str) -> set[str]:
    """
    >>> _n = lambda name: sorted(normalise_name(name))

    # UNEEDED? We don't use ROM names
    #>>> _n('alex kidd in miracle world (usa, europe) (v1.1).bin')
    #'alex kidd in miracle world'
    #>>> _n('animatix (infogrames) (j. pages, c. belin) (1985) (mo6 k7).k7')
    #'animatix'

    >>> _n('Alex Kidd in Miracle World (Euro, USA, v1)')
    ['alex kidd in miracle world']
    >>> _n('18 Wheeler (deluxe, Rev A)')
    ['18 wheeler']
    >>> _n('Yam! Yam!?')
    ['yam yam']
    >>> _n('U.S. Classic')
    ['u s classic']
    >>> _n('Vindicators Part II')
    ['vindicators part two']
    >>> _n('Touch & Go')
    ['touch and go']
    >>> _n('M.A.C.S. Basic Rifle Marksmanship (USA)')
    ['m a c s basic rifle marksmanship']

    Multipart names
    >>> _n('1941: Counter Attack (World 900227)')
    ['1941', '1941 counter attack', 'counter attack']
    >>> _n('X-Men: Children of the Atom (Euro 950331)')
    ['children of the atom', 'x men', 'x men children of the atom']
    >>> _n('Vampire Savior 2: The Lord of Vampire (Japan 970913)')
    ['the lord of vampire', 'vampire savior 2', 'vampire savior 2 the lord of vampire']
    >>> _n("Wonder Boy III - The Dragon's Trap (Euro, USA, Kor)")
    ['the dragons trap', 'wonder boy three', 'wonder boy three the dragons trap']
    >>> _n('Wonder Boy III - Monster Lair (set 6, World, System 16B) (8751 317-0098)')
    ['monster lair', 'wonder boy three', 'wonder boy three monster lair']
    >>> _n('Venom & Spider-Man - Separation Anxiety (SNES bootleg)')
    ['separation anxiety', 'venom and spider man', 'venom and spider man separation anxiety']
    >>> _n('Virtua Tennis 2 / Power Smash 2 (Rev A) (GDS-0015A)')
    ['power smash 2', 'virtua tennis 2', 'virtua tennis 2 power smash 2']
    >>> _n('Xtreme Rally / Off Beat Racer!')
    ['off beat racer', 'xtreme rally', 'xtreme rally off beat racer']
    >>> _n('Desert Strike - Return to the Gulf (Euro, USA)')
    ['desert strike', 'desert strike return to the gulf', 'return to the gulf']
    >>> _n('Shining Force - The Legacy of Great Intention (Euro)')
    ['shining force', 'shining force the legacy of great intention', 'the legacy of great intention']
    >>> _n('Star Trek - Deep Space Nine - Crossroads of Time (Euro)')
    ['crossroads of time', 'deep space nine', 'star trek', 'star trek deep space nine crossroads of time']
    >>> _n('World Rally 2: Twin Racing')
    ['twin racing', 'world rally 2', 'world rally 2 twin racing']


    Versus replacements
    >>> _n('X-Men Vs. Street Fighter (Euro 961004)')
    ['x men versus street fighter']
    >>> _n('Spider-Man vs. the Kingpin (World)')
    ['spider man versus the kingpin']

    Removed games
    >>> _n('Robocop 2 (handheld)')
    []
    >>> _n("Player's Edge Plus (IP0028) Joker Poker - French")
    []

    Preserving of known system names - VGMPlay system name normalisation
    >>> _n('Double Dragon (Neo-Geo)')
    ['double dragon neo geo']
    >>> _n('Aggressors of Dark Kombat (SNK Neo Geo)')
    ['aggressors of dark kombat neo geo']
    
    #>>> _n('Beatmania GB (Game Boy, Color)')
    #>>> _n('Beatmania GB Gatcha Mix2 (Game Boy Color)')
    #>>> _n('Blaster Master - Enemy Below (Nintendo Game Boy Color)')
    #>>> _n('Bomberman Collection (1996)(Hudson) (GameBoy)')
    #>>> _n('10-Yard Fight (NES)')
    #>>> _n('Beavis And Butt Head (GG)')

    Bear a Grudge (ZX Spectrum 128)
    Battle Squadron (GEN/MD)

    Battle Ace (PC Engine SuperGrafx)
    Batman (TG-16)
    Kaze no Densetsu Xanadu II (TG-CD)
    Nobunaga no Yabou - Bushou Fuunroku (PCE Super CD-ROM2)

    688 Attack Sub (IBM PC XT AT Tandy 1000)
    Alley Cat (IBM PCjr)
    Star Wars - X-Wing (IBM PC AT)

    Altered Beast (SMS-FM)
    Altered Beast (SMS-PSG)

    Antarctic Adventure (MSX)
    Antarctic Adventure (ColecoVision)
    After Burner II (Sharp X68000)
    SimCity 2000 (FM Towns)
    Vertical Force (Nintendo Virtual Boy)

    Ultima IV - Quest of the Avatar (Apple II)
    Star Wars - The Empire Strikes Back (NES)
    Street Fighter Alpha 3, Zero 3 (CP System II)
    NHL All-Star Hockey '95 (GEN/MD)
    Ristar - The Shooting Star (GEN/MD)
    Ristar The Shooting Star (GG)
    Parasol Stars - The Story of Bubble Bobble III (TG-16)

    Star Ship Rendezvous (MSX2)
    Sonyc (MSX2 FM)
    Sonyc (MSX2 Moonsound)
    Star Force (MSX)

    """
    name = name.lower()
    # Abort on excluded keywords
    for exclude_str in EXCLUDE_STR:
        if exclude_str in name:
            return {}
    #name = re.sub(r"(\..{1,4})$", '', name)  # Remove file extension
    name = re.sub(r"'", '', name)  # remove single quotes
    name = re.sub(r"\(neo[ -_]?geo.*\)", 'neo geo', name, flags=re.IGNORECASE)  # preserve neo geo in name
    name = re.sub(r'\(.*\)', '', name)  # remove items in parenthesis
    # Replacements
    name = re.sub(r'&', 'and', name)  # replace & with and
    name = re.sub(r' iii', ' three', name)  # replace roman numerals (CRUDE)
    name = re.sub(r' ii', ' two', name)
    name = re.sub(r' vs[. ]', ' versus ', name)  # replace pronunciation of versus

    def clean(name):
        # Tidy
        name = re.sub(r'\W', ' ', name)  # replace all non-alpha-numeric characters with space
        name = re.sub(r' +', ' ', name)  # compact multiple spaces down to a single space
        name = name.strip()
        return name

    names = tuple(clean(n) for n in re.split(r': | / | - ', name))
    return {*names, ' '.join(names)}



def prune_names_to_rom(iter_names):
    """
    >>> iter_names = (
    ...     ('Golden Axe (set 6, US, 8751 317-123A)', 'goldnaxe'),
    ...     ('Golden Axe - The Duel (JUETL 950117 V1.000)', 'gaxeduel'),
    ...     ('Golden Axe: The Revenge of Death Adder (World)', 'ga2'),
    ... )
    >>> prune_names_to_rom(iter_names)
    {'golden axe': 'goldnaxe', 'golden axe the duel': 'gaxeduel', 'the duel': 'gaxeduel', 'golden axe the revenge of death adder': 'ga2', 'the revenge of death adder': 'ga2'}
    """
    rom_to_names = {
        rom: normalise_name(name)
        for name, rom in iter_names
    }

    name_to_roms = defaultdict(set)
    for rom, names in rom_to_names.items():
        for name in names:
            name_to_roms[name].add(rom)

    def lowest_name_count_for_rom(roms):
        rom_name_count = {
            rom: len(rom_to_names[rom])
            for rom in roms
        }
        return min(rom_name_count, key=rom_name_count.get)
    return {
        name: lowest_name_count_for_rom(roms)
        for name, roms in name_to_roms.items()
    }

def save_names(name_to_rom, output_filename):
    with open(output_filename, 'wt') as output_filehandle:
        for name, rom in name_to_rom.items():
            output_filehandle.write(f'({name}):{rom}\n')



def mame_names():
    name_to_rom = prune_names_to_rom(
        iter_mame_names(lambda: _zip_filehandle('mamelx.zip'))
    )
    save_names(
        name_to_rom=name_to_rom,
        output_filename=os.path.join(PATH_OUTPUT, 'roms'),
    )

SYSTEMS = {
    'a2600',
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
        name_to_rom = prune_names_to_rom(
            iter_software_names(filehandle)
        )
        save_names(
            name_to_rom=name_to_rom,
            output_filename=os.path.join(PATH_OUTPUT, system_name),
        )


if __name__ == "__main__":
    #postmortem(main)
    os.makedirs(PATH_OUTPUT, exist_ok=True)
    mame_names()
    software_list_names()