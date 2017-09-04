import getopt
import logging
import os

import sys

from .po import PoDataSource, ContextPoDataSource
from .xliff import XliffDataSource
from .syncer import Syncer


SRC_TYPE_PO = 'po'
SRC_TYPE_PO_CONTEXT = 'poctxt'
SRC_TYPE_XLIFF = 'xliff'


def main():
    doc = None
    src_type = 'po'
    src_dir = None
    domain = None
    sheet = None
    secret = None
    verbose = False

    opts, args = getopt.getopt(sys.argv[1:], 'o:', ['src-type=', 'src-dir=', 'use-ctxt', 'podir=', 'domain=', 'secret=', 'doc=', 'sheet=', 'verbose'])
    for o, a in opts:
        if o == '--src-type':
            src_type = a
        elif o == '--use-ctxt':
            src_type = SRC_TYPE_PO_CONTEXT
        elif o in {'--src-dir', '--podir'}:
            src_dir = a
        elif o == '--domain':
            domain = a
        elif o == '--secret':
            secret = a
        elif o == '--doc':
            doc = a
        elif o == '--sheet':
            sheet = a
        elif o == '--verbose':
            verbose = True

    if src_dir is None or secret is None or doc is None or sheet is None:
        raise Exception('no src-dir, secret, doc nor sheet')

    if domain is None:
        domain = os.path.basename(src_dir)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    if src_type == SRC_TYPE_PO:
        datasource = PoDataSource(src_dir)
    elif src_type == SRC_TYPE_PO_CONTEXT:
        datasource = ContextPoDataSource(src_dir)
    elif src_type == SRC_TYPE_XLIFF:
        datasource = XliffDataSource(src_dir)
    else:
        raise Exception('unknown src-type: {}'.format(src_type))

    Syncer(datasource, domain, secret, doc, sheet).run()

if __name__ == '__main__':
    main()
