import sys
from collections import OrderedDict
from tempfile import TemporaryDirectory

from plenum.cli.cli import Cli
from plenum.common.looper import Looper
from plenum.common.util import getConfig


def main(logfile: str=None, debug=None, cliClass=None):
    config = getConfig()
    nodeReg = config.nodeReg
    cliNodeReg = config.cliNodeReg
    basedirpath = config.baseDir

    if not cliClass:
        cliClass = Cli

    with Looper(debug=False) as looper:
        cli = cliClass(looper=looper,
                       basedirpath=basedirpath,
                       nodeReg=nodeReg,
                       cliNodeReg=cliNodeReg,
                       logFileName=logfile,
                       debug=debug)

        if not debug:
            looper.run(cli.shell(*sys.argv[1:]))
            print('Goodbye.')
        return cli

if __name__ == '__main__':
    main()
