import glob
import logging
import xml.etree.ElementTree as ET

import os

import sys

from .syncer import DataSource

_XLIFF_NAMESPACE = 'urn:oasis:names:tc:xliff:document:1.2'


def _get_tag(tag):
    return '{{{}}}{}'.format(_XLIFF_NAMESPACE, tag)


def _to_sheet_lang(lang):
    if lang == 'zh-Hans':
        return 'zh_CN'
    elif lang == 'zh-Hant':
        return 'zh_TW'
    else:
        return lang


def _from_sheet_lang(sheet_lang):
    if sheet_lang == 'zh_CN':
        return 'zh-Hans'
    elif sheet_lang == 'zh_TW':
        return 'zh-Hant'
    else:
        return sheet_lang


def _is_excluded_id(trans_id):
    return trans_id in {'CFBundleShortVersionString'}


def _is_special_key(key):
    if len(key.strip()) == 0:
        return True
    elif key.startswith('$('):
        return True
    elif key.startswith('[D] '):
        return True
    return False


def _import_special_key(key):
    if key.startswith('$('):
        return None
    elif key.startswith('[D] '):
        return key[4:]
    return key


def _is_special_trans(trans):
    if trans == '$$no translation$$':
        return True
    return False


def _apply_special_trans(key, trans, langtransmap):
    if trans == '$$no translation$$':
        return key
    return langtransmap.get('en', {}).get(key, key)


class XliffDataSource(DataSource):
    def __init__(self, xliffdir):
        self.treemap = {}
        self.xliffdir = xliffdir

        ET.register_namespace('', _XLIFF_NAMESPACE)
        for file_path in glob.glob(os.path.join(self.xliffdir, '*.xliff')):
            lang = os.path.splitext(os.path.basename(file_path))[0]
            tree = ET.parse(file_path)
            self.treemap[lang] = tree

    def exporttrans(self):
        langtransmap = {}
        for lang, tree in self.treemap.iteritems():
            sheet_lang = _to_sheet_lang(lang)
            langtransmap[sheet_lang] = {}
            for src_file in tree.findall(_get_tag('file')):
                for trans_unit in src_file.findall('.//{}'.format(_get_tag('trans-unit'))):
                    if _is_excluded_id(trans_unit.get('id')):
                        continue

                    source = trans_unit.find(_get_tag('source'))
                    target = trans_unit.find(_get_tag('target'))

                    key = source.text if source is not None else ''
                    trans = target.text if target is not None else ''

                    if _is_special_key(key):
                        continue

                    if trans.startswith('~'):
                        trans = ''

                    if key == trans:
                        langtransmap[sheet_lang][key] = ''
                    else:
                        langtransmap[sheet_lang][key] = trans

        return langtransmap

    def importtrans(self, langtransmap):
        en_update_map = {}
        for lang, tree in self.treemap.iteritems():
            sheet_lang = _to_sheet_lang(lang)
            if sheet_lang in langtransmap:
                transmap = langtransmap[sheet_lang]
                for src_file in tree.findall(_get_tag('file')):
                    for trans_unit in src_file.findall('.//{}'.format(_get_tag('trans-unit'))):
                        if _is_excluded_id(trans_unit.get('id')):
                            continue

                        source = trans_unit.find(_get_tag('source'))
                        target = trans_unit.find(_get_tag('target'))

                        key = source.text if source is not None else ''

                        if lang == 'en':
                            trans = transmap.get(key)
                            if _is_special_trans(trans):
                                continue
                            if trans and key != trans:
                                en_update_map[key] = trans
                            continue

                        if _is_special_key(key):
                            trans = _import_special_key(key)
                            if trans is not None:
                                if target is None:
                                    target = ET.SubElement(trans_unit, _get_tag('target'))
                                target.text = trans
                        else:
                            if target is None:
                                target = ET.SubElement(trans_unit, _get_tag('target'))
                            trans = transmap.get(key) or u'~{}'.format(key)
                            if _is_special_trans(trans):
                                trans = _apply_special_trans(key, trans, langtransmap)
                            oldtrans = target.text
                            if oldtrans != trans:
                                logging.info(u'[{}] Updating xliff of {}: {} -> {}'.format(lang, key, oldtrans, trans))
                                target.text = trans

            if len(en_update_map) > 0:
                continue

            file_path = os.path.join(self.xliffdir, lang + ".xliff")
            tree.write(file_path, encoding='UTF-8', xml_declaration=True)

        if len(en_update_map) > 0:
            for key, trans in en_update_map.iteritems():
                logging.warn(u'[en] English changes should be applied manually: {} -> {}'.format(key, trans))
            logging.warn(u'[en] Apply English changes and try again')
            sys.exit(os.EX_TEMPFAIL)
