#@+leo-ver=5-thin
#@+node:btheado.20191227180740.1: * @file conf_test.py
#@+others
#@+node:btheado.20191227180805.1: ** imports
import leo.core.leoBridge as leoBridge
import pytest
#@+node:btheado.20191227180831.1: ** bridge fixture
@pytest.fixture(scope="session")
def bridge():
    return leoBridge.controller(gui='nullGui',
        loadPlugins=False, readSettings=False,
        silent=False, verbose=False)
#@+node:btheado.20191227180839.1: ** tree fixtures
#
# All pytest function arguments must match a fixture name. Here
# fixtures are defined for various test tree structures. The fixtures
# are named such that the structure of the tree can be determined
# by looking at the name.
#
# The tree names consist of document order names of leaf nodes
# separated by an underscore
#
# nodes in the first level of the tree are named by numbers (1,2,3,...)
# nodes in the second level of the tree are named by their parent
# plus their relative position as indicated by lower case letters 
# (1a, 1b, 1c, ..., 2a, 2b, ...)
#
# The nodes in each level thereafter alternate being identified by
# numbers and letters
#
# So a tree with this structure:
# - 1
#    - a
#       - 1
#       - 2
#     - b
# - 2
#
# Has the name: tree_1a1_1a2_1b_2
#
# As an additional shorthand, leaf nodes which have following
# siblings can be omitted from the name of the tree. In the above
# example node 1a1 is childless and has a following sibling and can
# therefore be omitted. So a shorter synonym for that tree is:
# tree_1a2_1b_2
#
# The name of a cloned node consists of the names of each node
# as if they were not cloned listed in document order and joined
# by the capital letter C. So if the nodes at the paths 1a1 and 1a2
# are clones of each other, then their names will both be 1a1C1a2.
# Hmm, but this isn't enough. I think it still needs the path of the
# actual node. So the clone at 1a1 would be 1a1C1a1C1a2 and 
# the one at 1a2 would be 1a2C1a1C1a2
#
# Would be useful to also have support for @file nodes. I think it
# would be enough to just prefix the particular node name with
# @file string. If I had that, then it would be enough to test the
# #1451 changes...have a before test illustrating the bug and an
# after test showing it is fixed and maybe an xfail test showing the
# functionality which is lost.
#@+others
#@+node:btheado.20191227180839.2: *3* tree_1
@pytest.fixture
def tree_1(bridge, tmpdir):
    """ Simple tree with just a single node """
    c = bridge.openLeoFile(str(tmpdir.join("tree_1.leo")))
    p = c.rootPosition()
    p.h = "1"
    p.b = "b_1"
    return c
#@+node:btheado.20191227180839.3: *3* tree_1b
@pytest.fixture
def tree_1b(bridge,tmpdir):
    """ A simple tree with one root having two children """
    c = bridge.openLeoFile(str(tmpdir.join("treee_1b.leo")))
    p = c.rootPosition()
    p.h = "1"
    p.b = "b_1"

    p1 = p.insertAsLastChild()
    p1.h = "1a"
    p1.b = "b_1a"
    p2 = p1.insertAfter()
    p2.h = "1b"
    p2.b = "b_1b"
    return c
#@+node:btheado.20191227180854.1: *3* tree_F1 (@file)
@pytest.fixture
def tree_F1(bridge, tmpdir):
    """
        Simple one node tree with an @file matching name of the node
    """
    c = bridge.openLeoFile(str(tmpdir.join("tree_F1.leo")))
    p = c.rootPosition()
    p.h = "@file 1"
    p.b = "b_1"
    return c
#@+node:btheado.20191227180920.1: *3* tree_A1 (@asis)
@pytest.fixture
def tree_A1(bridge, tmpdir):
    """
        Simple one node tree with an @file matching name of the node
    """
    c = bridge.openLeoFile(str(tmpdir.join("tree_A1.leo")))
    p = c.rootPosition()
    p.h = "@asis 1"
    p.b = "b_1"
    return c
#@-others
#@-others
#@-leo
