import getopt
import logging
import os

import sys

from .po import PoDataSource
from .syncer import Syncer


def main():
    doc = None
    podir = None
    domain = None
    sheet = None
    secret = None
    verbose = False

    opts, args = getopt.getopt(sys.argv[1:], 'o:', ['podir=', 'domain=', 'secret=', 'doc=', 'sheet=', 'verbose'])
    for o, a in opts:
        if o in ('--podir', ):
            podir = a
        elif o in ('--domain', ):
            domain = a
        elif o in ('--secret', ):
            secret = a
        elif o in ('--doc', ):
            doc = a
        elif o in ('--sheet', ):
            sheet = a
        elif o in ('--verbose', ):
            verbose = True

    if podir is None or secret is None or doc is None or sheet is None:
        raise Exception('no podir, secret, doc nor sheet')

    if domain is None:
        domain = os.path.basename(podir)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    datasource = PoDataSource(podir)
    Syncer(datasource, domain, secret, doc, sheet).run()

if __name__ == '__main__':
    main()
