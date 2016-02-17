import logging
from typing import Iterable, Optional

from zeno.common.looper import Looper
from zeno.test.eventually import eventually
from zeno.test.greek import genNodeNames

from zeno.common.startable import Status
from zeno.test.helper import TestNodeSet, JOINED_NOT_ALLOWED, CONNECTED, \
    checkNodeRemotes, addNodeBack, ordinal, \
    checkNodesConnected

whitelist = ['discarding message']


# noinspection PyIncorrectDocstring
def testProtocolInstanceCannotBecomeActiveWithLessThanFourServers(
        tdir_for_func):
    """
    A protocol instance must have at least 4 nodes to come up.
    The status of the nodes will change from starting to started only after the
    addition of the fourth node to the system.
    """
    nodeCount = 16
    f = 5
    minimumNodesToBeUp = 16 - f

    nodeNames = genNodeNames(nodeCount)
    with TestNodeSet(names=nodeNames, tmpdir=tdir_for_func) as nodeSet:
        with Looper(nodeSet) as looper:

            for n in nodeSet:
                n.startKeySharing()

            # helpers

            def genExpectedStates(connecteds: Iterable[str]):
                return {
                    nn: CONNECTED if nn in connecteds else JOINED_NOT_ALLOWED
                    for nn in nodeNames}

            def checkNodeStatusRemotesAndF(expectedStatus: Status,
                                           nodeIdx: int):
                for node in nodeSet.nodes.values():
                    checkNodeRemotes(node,
                                     genExpectedStates(nodeNames[:nodeIdx + 1]))
                    assert node.status == expectedStatus

            def addNodeBackAndCheck(nodeIdx: int, expectedStatus: Status):
                logging.info("Add back the {} node and see status of {}".
                             format(ordinal(nodeIdx + 1), expectedStatus))
                addNodeBack(nodeSet, looper, nodeNames[nodeIdx])
                looper.run(
                        eventually(checkNodeStatusRemotesAndF, expectedStatus,
                                   nodeIdx,
                                   retryWait=1, timeout=30))

            # tests

            logging.debug("Sharing keys")
            looper.run(checkNodesConnected(nodeSet))

            logging.debug("Remove all the nodes")
            for n in nodeNames:
                looper.removeProdable(nodeSet.nodes[n])
                nodeSet.removeNode(n, shouldClean=False)

            logging.debug("Add nodes back one at a time")
            for i in range(nodeCount):
                nodes = i + 1
                if nodes < minimumNodesToBeUp:
                    expectedStatus = Status.starting
                elif nodes < nodeCount:
                    expectedStatus = Status.started_hungry
                else:
                    expectedStatus = Status.started
                addNodeBackAndCheck(i, expectedStatus)