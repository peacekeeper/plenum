import os
from collections import OrderedDict

from raet.nacling import Signer, Privateer
from raet.road.keeping import RoadKeep


def initLocalKeep(name, baseDir, pkseed, sigseed, override=False):
    """
    Initialize RAET local keep. Write local role data to file.

    :param name: name of the node
    :param baseDir: base directory
    :param pkseed: seed to generate public and private key pair
    :param sigseed: seed to generate signing and verification key pair
    :param override: overwrite the local role.json file if already exists
    :return: tuple(public key, verification key)
    """
    rolePath = os.path.join(baseDir, name, "role", "local", "role.json")
    if os.path.isfile(rolePath):
        if not override:
            raise FileExistsError("Keys exists for local role {}".format(name))

    if not isinstance(pkseed, bytes):
        pkseed = pkseed.encode()
    if not isinstance(sigseed, bytes):
        sigseed = sigseed.encode()

    priver = Privateer(pkseed)
    signer = Signer(sigseed)
    keep = RoadKeep(stackname=name, baseroledirpath=baseDir)
    prikey, pubkey = priver.keyhex, priver.pubhex
    sigkey, verkey = signer.keyhex, signer.verhex
    data = OrderedDict([
        ("role", name),
        ("prihex", prikey),
        ("sighex", sigkey)
    ])
    keep.dumpLocalRoleData(data)
    return pubkey.decode(), verkey.decode()


def initRemoteKeep(name, remoteName, baseDir, pubkey, verkey, override=False):
    """
    Initialize RAET remote keep

    :param name: name of the node
    :param remoteName: name of the remote to store keys for
    :param baseDir: base directory
    :param pubkey: public key of the remote
    :param verkey: private key of the remote
    :param override: overwrite the role.remoteName.json file if it already
    exists.
    """
    rolePath = os.path.join(baseDir, name, "role", "remote", "role.{}.json".
                            format(remoteName))
    if os.path.isfile(rolePath):
        if not override:
            raise FileExistsError("Keys exists for remote role {}".
                                  format(remoteName))

    keep = RoadKeep(stackname=name, baseroledirpath=baseDir)
    data = OrderedDict([
        ('role', remoteName),
        ('acceptance', 1),
        ('pubhex', pubkey),
        ('verhex', verkey)
    ])
    keep.dumpRemoteRoleData(data, role=remoteName)


def hasKeys(data, keynames):
    """
    Checks whether all keys are present in the given data, and are not None
    """
    # if all keys in `keynames` are not present in `data`
    if len(set(keynames).difference(set(data.keys()))) != 0:
        return False
    for key in keynames:
        if data[key] is None:
            return False
    return True


def isLocalKeepSetup(name, baseDir=None) -> bool:
    """
    Check that the local RAET keep has the values of role, sighex and prihex
    populated for the given node

    :param name: the name of the node to check the keys for
    :param baseDir: base directory of Plenum
    :return: whether the keys are setup
    """
    keep = RoadKeep(stackname=name, baseroledirpath=baseDir)
    localRoleData = keep.loadLocalRoleData()
    return hasKeys(localRoleData, ['role', 'sighex', 'prihex'])
