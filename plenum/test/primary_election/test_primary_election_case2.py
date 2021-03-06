import pytest

from plenum.server.suspicion_codes import Suspicions
from plenum.test.eventually import eventually
from plenum.test.helper import TestNodeSet, checkNodesConnected, \
    ensureElectionsDone, \
    delayerMsgTuple

from plenum.common.types import Nomination
from plenum.server.replica import Replica
from plenum.test.primary_election.helpers import checkNomination, \
    getSelfNominationByNode

nodeCount = 4
whitelist = ['already got nomination',
             'doing nothing for now']


@pytest.fixture()
def case2Setup(startedNodes: TestNodeSet):
    A, B, C, D = startedNodes.nodes.values()

    # Node B delays self nomination so A's nomination reaches everyone
    B.delaySelfNomination(5)
    # Node B delays nomination from all nodes
    B.nodeIbStasher.delay(delayerMsgTuple(5, Nomination))

    for node in [C, D]:
        # Also Nodes C and D are slow so they will not nominate for themselves
        # for long
        node.delaySelfNomination(25)

    # A, C and D should not blacklist B since we are trying to check if
    # multiple nominations from the same node have any impact on
    # the election
    for node in A, C, D:
        node.whitelistNode(B.name, Suspicions.DUPLICATE_NOM_SENT.code)


# noinspection PyIncorrectDocstring
def testPrimaryElectionCase2(case2Setup, looper, keySharedNodes):
    """
    Case 2 - A node making nominations for a multiple other nodes. Consider 4
    nodes A, B, C, and D. Lets say node B is malicious and nominates node C
    to all nodes. Again node B nominates node D to all nodes.
    """
    nodeSet = keySharedNodes
    A, B, C, D = nodeSet.nodes.values()

    looper.run(checkNodesConnected(nodeSet))

    # Node B sends multiple NOMINATE msgs but only after A has nominated itself
    looper.run(eventually(checkNomination, A, A.name, retryWait=.25, timeout=1))

    instId = getSelfNominationByNode(A)

    BRep = Replica.generateName(B.name, instId)
    CRep = Replica.generateName(C.name, instId)
    DRep = Replica.generateName(D.name, instId)

    # Node B first sends NOMINATE msgs for Node C to all nodes
    B.send(Nomination(CRep, instId, B.viewNo))
    # Node B sends NOMINATE msgs for Node D to all nodes
    B.send(Nomination(DRep, instId, B.viewNo))

    # Ensure elections are done
    ensureElectionsDone(looper=looper, nodes=nodeSet, retryWait=1, timeout=45)

    # All nodes from node A, node C, node D(node B is malicious anyway so
    # not considering it) should have nomination for node C from node B since
    #  node B first nominated node C
    for node in [A, C, D]:
        assert node.elector.nominations[instId][BRep] == CRep
