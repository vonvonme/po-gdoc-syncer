from unittest import TestCase

from posyncer.po import ContextPoDataSource
from posyncer.syncer import Syncer


class TestContext(TestCase):
    def setUp(self):
        self.podir = 'sample/android'

    def test_exporttrans(self):
        datasource = ContextPoDataSource(self.podir)
        langtransmap = datasource.exporttrans()
        self.assertIn('default', langtransmap)
        self.assertIn('ko', langtransmap)
        for ctxt, s in langtransmap['default'].iteritems():
            self.assertIn(ctxt, langtransmap['ko'])
        for ctxt, s in langtransmap['ko'].iteritems():
            self.assertIn(ctxt, langtransmap['default'])

    def test_sync(self):
        datasource = ContextPoDataSource(self.podir)
        Syncer(datasource, 'android', '../../peachy/tools/client_secret.json',
               'vonvon-translate-temp', 'translate-peachy').run()

    def test_importtrans(self):
        self.fail()
