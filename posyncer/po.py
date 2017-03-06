import glob
import logging
import os

import polib

from .syncer import DataSource


class PoDataSource(DataSource):
    def __init__(self, podir):
        self.pomap = {}
        self.podir = podir

        for pofile in glob.glob(os.path.join(self.podir, '*.po')):
            po = polib.pofile(pofile)
            lang = os.path.splitext(os.path.basename(pofile))[0]
            self.pomap[lang] = po

    def exporttrans(self):
        langtransmap = {}
        for lang, po in self.pomap.iteritems():
            langtransmap[lang] = {}
            for entry in po:
                langtransmap[lang][entry.msgid] = entry.msgstr

        return langtransmap

    def importtrans(self, langtransmap):
        for lang, po in self.pomap.iteritems():
            if lang in langtransmap:
                transmap = langtransmap[lang]
                for entry in po:
                    key = entry.msgid
                    oldtrans = entry.msgstr
                    trans = transmap.get(key)
                    if oldtrans != trans:
                        logging.info(u'[{}] Updating po of {}: {} -> {}'.format(lang, key, oldtrans, trans))
                        entry.msgstr = trans

            file_path = os.path.join(self.podir, lang + ".po")
            po.save(file_path)


class ContextPoDataSource(DataSource):
    pomap = {}

    def __init__(self, podir):
        self.pomap = {}
        self.podir = podir

        for pofile in glob.glob(os.path.join(self.podir, '*.pot')):
            po = polib.pofile(pofile)
            lang = 'default'
            if lang in self.pomap:
                raise ValueError('2 or more pot file in podir')
            self.pomap[lang] = po

        for pofile in glob.glob(os.path.join(self.podir, '*.po')):
            po = polib.pofile(pofile)
            lang = os.path.splitext(os.path.basename(pofile))[0]
            self.pomap[lang] = po

    def exporttrans(self):
        langtransmap = {}
        for lang, po in self.pomap.iteritems():
            langtransmap[lang] = {}
            for entry in po:
                if lang == 'default':
                    langtransmap[lang][entry.msgctxt] = entry.msgid
                else:
                    langtransmap[lang][entry.msgctxt] = entry.msgstr

        return langtransmap

    def importtrans(self, langtransmap):
        if 'default' not in self.pomap:
            raise ValueError('no pot entry in langtransmap')

        for lang, po in self.pomap.iteritems():
            if lang in langtransmap:
                transmap = langtransmap[lang]
                if lang == 'default':
                    for entry in po:
                        key = entry.msgctxt
                        oldtrans = entry.msgid
                        trans = transmap.get(key)
                        if oldtrans != trans:
                            logging.info(u'[{}] Updating pot of {}: {} -> {}'.format(lang, key, oldtrans, trans))
                            entry.msgid = trans
                else:
                    for entry in po:
                        key = entry.msgctxt
                        oldtrans = entry.msgstr
                        trans = transmap.get(key)
                        if oldtrans != trans:
                            logging.info(u'[{}] Updating po of {}: {} -> {}'.format(lang, key, oldtrans, trans))
                            entry.msgstr = trans
                        if entry.msgid != langtransmap['default'].get(key):
                            entry.msgid = langtransmap['default'][key]

            if lang == 'default':
                file_path = os.path.join(self.podir, "template.pot")
            else:
                file_path = os.path.join(self.podir, lang + ".po")
            po.save(file_path)
