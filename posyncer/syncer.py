import logging
import webbrowser
import gspread
from oauth2client import client
try:
    from oauth2client.contrib.keyring_storage import Storage
except ImportError:
    from oauth2client.keyring_storage import Storage

__author__ = 'eungkyu'


class MsgEntry(object):
    def __init__(self, msgstr, occurs=None):
        self.msgstr = msgstr
        self.occurs = occurs


class DataSource(object):
    def exporttrans(self):
        """
        :return: should return lang -> key -> value dict
        """
        raise NotImplementedError('Should have implemented this')

    def importtrans(self, langtransmap):
        """
        should save lang -> key -> value dict to original data
        """
        raise NotImplementedError('Should have implemented this')


class Syncer:
    def __init__(self, datasource, domain, secret_file, docname, sheetname):
        self.datasource = datasource
        self.domain = domain
        self.secret_file = secret_file
        self.sheetname = sheetname
        self.docname = docname
        self.worksheet = None
        self.sourcecol = None
        self.tagcol = None
        self.targetcolmap = {}
        self.all_values = None

    def run(self):
        spreadsheet = self._open_spreadsheet()
        self.worksheet = spreadsheet.worksheet(self.sheetname)

        logging.info(u'Loading sheet {}'.format(self.sheetname))
        self.all_values = self.worksheet.get_all_values()
        logging.info('... {} rows'.format(len(self.all_values)))

        langtransmap = self.datasource.exporttrans()
        sourcetargetmap = self._readsheet()

        Syncer._update_target(langtransmap, sourcetargetmap)
        self._apply_trans(langtransmap, sourcetargetmap)

        self._updatesheet(sourcetargetmap)
        self.datasource.importtrans(langtransmap)

    def _open_spreadsheet(self):
        gc = self._authorize()
        logging.info(u'Opening document {}'.format(self.docname))
        return gc.open(self.docname)

    def _authorize(self):
        storage = Storage('po-gdoc-syncer', 'user')
        try:
            credentials = storage.get()
            logging.info(u'Authorizing from keychain')
            return gspread.authorize(credentials)
        except Exception as e:
            logging.info(u'Initiating new authorization flow')
            flow = client.flow_from_clientsecrets(self.secret_file, 'https://spreadsheets.google.com/feeds',
                                                  redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_uri = flow.step1_get_authorize_url()
            webbrowser.open(auth_uri)

            auth_code = raw_input('Enter the auth code: ')

            credentials = flow.step2_exchange(auth_code)
            storage.put(credentials)
            return gspread.authorize(credentials)

    def _readsheet(self):
        sourcetargetmap = {}

        keys = self.all_values[0]
        for col, key in enumerate(keys):
            if key == 'source':
                self.sourcecol = col
            elif key == 'tag':
                self.tagcol = col
            elif key.startswith('target-'):
                self.targetcolmap[key] = col

        for row in self.all_values[1:]:
            source = row[self.sourcecol]
            tag = set(row[self.tagcol].split(u','))
            tag.discard('')
            tag.discard('OK')
            tag.discard('UNUSED')
            tag.discard(self.domain)

            if not source:
                raise Exception('no source for row: {}'.format(row))

            sourcetargetmap[source] = {'tag': tag}
            for target, col in self.targetcolmap.iteritems():
                value = row[col]
                sourcetargetmap[source][target] = value

        return sourcetargetmap

    def _updatesheet(self, sourcetargetmap):
        for rownum, row in enumerate(self.all_values[1:]):
            source = row[self.sourcecol]
            tag = row[self.tagcol]

            if source in sourcetargetmap:
                targetmap = sourcetargetmap[source]
                newtag = ','.join(sorted(targetmap['tag'])) or 'UNUSED'
                if tag != newtag:
                    logging.info(u'Setting tag of {}: {}'.format(source, newtag))
                    self.worksheet.update_cell(rownum + 2, self.tagcol + 1, newtag)

                for target, col in self.targetcolmap.iteritems():
                    value = row[col]
                    newvalue = sourcetargetmap[source][target]
                    if value != newvalue:
                        logging.info(u'[{}] Updating value of {}: {} -> {}'.format(target, source, value, newvalue))
                        self.worksheet.update_cell(rownum + 2, col + 1, newvalue)

                del sourcetargetmap[source]

        for source, targetmap in sourcetargetmap.iteritems():
            row = [''] * len(self.all_values[0])
            row[self.sourcecol] = source
            row[self.tagcol] = ','.join(sorted(targetmap['tag'])) or 'UNUSED'

            for target, value in targetmap.iteritems():
                if target == 'tag':
                    continue
                if target not in self.targetcolmap:
                    logging.warn(u'Ignoring {}: no column'.format(target))
                    continue
                row[self.targetcolmap[target]] = value
            logging.info(u'Appending row of {}'.format(source))
            self.worksheet.append_row(row)

    @staticmethod
    def _update_target(langtransmap, sourcetargetmap):
        for lang, transmap in langtransmap.iteritems():
            for key, trans in transmap.iteritems():
                target = 'target-' + lang
                if key not in sourcetargetmap:
                    sourcetargetmap[key] = {'tag': set()}
                if target not in sourcetargetmap[key]:
                    sourcetargetmap[key][target] = ''

                if trans and not sourcetargetmap[key][target]:
                    sourcetargetmap[key][target] = trans

    def _apply_trans(self, langtransmap, sourcetargetmap):
        for source, targetmap in sourcetargetmap.iteritems():
            for target, value in targetmap.iteritems():
                if target == 'tag':
                    continue

                lang = target[7:]
                if lang in langtransmap and source in langtransmap[lang]:
                    targetmap['tag'].add(self.domain)
                    if value and value != '$needs translation$$':
                        langtransmap[lang][source] = value

