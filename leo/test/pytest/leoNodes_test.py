#@+leo-ver=5-thin
#@+node:btheado.20191203182713.1: * @file leoNodes_test.py
# Run with ~/src/pyqt-3.7-venv/bin/pytest -W ignore::DeprecationWarning --cov=leo.core.leoNodes  --cov-report html --cov-report term-missing leo/test/pytest/leoNodes_test.py
#@+others
#@+node:btheado.20191203213715.1: ** imports
import pytest
import leo.core.leoNodes as leoNodes
#@+node:btheado.20191204164352.1: ** subtree, children and siblings tests
def test_subtree(tree_1b):
    p1 = tree_1b.rootPosition()
    assert p1.h == "1"
    assert [p.h for p in p1.subtree()] == ["1a", "1b"]

def test_self_and_subtree(tree_1b):
    p1 = tree_1b.rootPosition()
    assert [p.h for p in p1.self_and_subtree()] == ["1", "1a", "1b"]

def test_self_and_siblings(tree_1b):
    p1 = tree_1b.rootPosition()
    assert [p.h for p in p1.self_and_siblings()] == ["1"]

def test_children(tree_1b):
    p1 = tree_1b.rootPosition()
    assert [p.h for p in p1.children()], ['1a', '1b']

def test_following_siblings(tree_1b):
    p1 = tree_1b.rootPosition()
    p1a = next(p1.children())
    assert [p.h for p in p1.following_siblings()] == []
    assert [p.h for p in p1a.following_siblings()] == ['1b']
#@+node:btheado.20191204174719.1: ** comparison tests
#@+node:btheado.20191227135931.1: *3* test_eq
def test_eq(tree_1b):
    p = tree_1b.rootPosition()
    assert p == p
    assert p >= p
    assert p <= p
    assert next(p.subtree()) != p
    assert p != p.v
#@+node:btheado.20191227135940.1: *3* test_eq_subclass
@pytest.mark.xfail(reason="Method returns exception instead of raising it. Bug?")
def test_eq_subclass(tree_1):
    v = leoNodes.vnode(tree_1)
    class MyPosition(leoNodes.Position):
        pass
    p1 = leoNodes.Position(v=v)
    p2 = MyPosition(v=v)
    # I expected this to throw a NotImplementedError, but the code
    # is actually returning the class insted of throwing it. Bug? Seems
    # like it has to be a bug since python will try to cast the result to
    # a boolean which will work, but doesn't seem useful for anything.
    with pytest.raises(NotImplementedError):
        assert p2 == p1
#@+node:btheado.20191227135947.1: *3* test_lt
def test_lt(tree_1b):
    p1 = tree_1b.rootPosition()
    for p in p1.subtree():
        # root occurs earlier than rest of subtree
        assert p1 < p
#@+node:btheado.20191227135950.1: *3* test_children_gt
def test_children_gt(tree_1b):
    root = tree_1b.rootPosition()
    for p in root.subtree():
        # root occurs earlier than rest of subtree
        assert p > root
#@+node:btheado.20191227135953.1: *3* test_following_sibling_gt
def test_following_sibling_gt(tree_1b):
    root1 = tree_1b.rootPosition()
    root2 = root1.insertAfter()
    assert root2 > root1
#@+node:btheado.20191227135957.1: *3* test_nonroot_siblings_gt
def test_nonroot_siblings_gt(tree_1b):
    root = tree_1b.rootPosition()
    s1,s2 = list(root.subtree())[0:2]
    assert s2 > s1
#@+node:btheado.20191227140002.1: *3* test_cousins_gt_and_lt
def test_cousins_gt_and_lt(tree_1b):
    root1 = tree_1b.rootPosition()
    cousin1 = next(root1.subtree())
    root2 = root1.insertAfter()
    cousin2 = root2.insertAsLastChild()
    assert cousin2 > cousin1
    assert cousin1 < cousin2
#@+node:btheado.20191204215348.1: ** test_more_serialize
def test_more_serialize(tree_1b):
    root = tree_1b.rootPosition()
    root.b = "+body"  ;# Adding a plus to test escaping
    assert root.convertTreeToString() =="""\
+ 1
\\+body
\t- 1a
b_1a
\t- 1b
b_1b
"""
#@+node:btheado.20191208143127.1: ** p.findRootPosition()
def test_findRootPosition(tree_1b):
    p1 = tree_1b.rootPosition()
    assert [p.findRootPosition().h for p in p1.children()], ['1', '1']
#@+node:btheado.20191208143402.1: ** p.isAncestorOf
def test_isAncestorOf(tree_1b):
    p1 = tree_1b.rootPosition()
    assert [p1.isAncestorOf(p) for p in p1.children()] == [True, True]
    assert not(p1.copy().moveToFirstChild().isAncestorOf(p1.moveToLastChild()))

def test_isAncestorOf2(tree_1b, tree_1):
    t1p1 = tree_1b.rootPosition()
    t2p1 = tree_1.rootPosition()
    assert not(t1p1.isAncestorOf(t2p1))
#@+node:btheado.20191209201021.1: ** p.nearest_roots
#@+node:btheado.20191210210145.1: *3* test_nearest_roots_none
def test_nearest_roots_none(tree_1b):
    p = tree_1b.rootPosition() # 1
    assert list(p.nearest_roots()) == []
    p.moveToFirstChild() # 1a
    assert list(p.nearest_roots()) == []
    def never(p): return False
    assert list(p.nearest_roots(predicate= never)) == []
#@+node:btheado.20191210210151.1: *3* test_nearest_roots_self
def test_nearest_roots_self(tree_1b):
    p = tree_1b.rootPosition() # 1
    p.moveToFirstChild() # 1a
    def always(p): return True
    assert [p.h for p in p.nearest_roots(predicate=always)] == ["1a"]
#@+node:btheado.20191210210156.1: *3* test_nearest_roots_ancestor
def test_nearest_roots_ancestor(tree_1b):
    p = tree_1b.rootPosition() # 1
    p.moveToFirstChild() # 1a
    def p1(p): return p.h == '1'
    assert [p.h for p in p.nearest_roots(predicate=p1)] == ["1"]
#@+node:btheado.20191210210201.1: *3* test_nearest_roots_children
def test_nearest_roots_children(tree_1b):
    p = tree_1b.rootPosition()  # 1
    def child(p): return p.h in ["1a", "1b"]
    assert [p.h for p in p.nearest_roots(predicate=child)] == ["1a", "1b"]
#@+node:btheado.20191210210300.1: ** p.nearest_unique_roots
#@+node:btheado.20191210210300.2: *3* test_nearest_unique_roots_none
def test_nearest_unique_roots_none(tree_1b):
    p = tree_1b.rootPosition() # 1
    assert list(p.nearest_unique_roots()) == []
    p.moveToFirstChild() # 1a
    assert list(p.nearest_unique_roots()) == []
    def never(p): return False
    assert list(p.nearest_unique_roots(predicate= never)) == []
#@+node:btheado.20191210210300.3: *3* test_nearest_unique_roots_self
def test_nearest_unique_roots_self(tree_1b):
    p = tree_1b.rootPosition() # 1
    p.moveToFirstChild() # 1a
    def always(p): return True
    assert [p.h for p in p.nearest_unique_roots(predicate=always)] == ["1a"]
#@+node:btheado.20191210210300.4: *3* test_nearest_unique_roots_ancestor
def test_nearest_unique_roots_ancestor(tree_1b):
    p = tree_1b.rootPosition() # 1
    p.moveToFirstChild() # 1a
    def p1(p): return p.h == '1'
    assert [p.h for p in p.nearest_unique_roots(predicate=p1)] == ["1"]
#@+node:btheado.20191210210300.5: *3* test_nearest_unique_roots_children
def test_nearest_unique_roots_children(tree_1b):
    p = tree_1b.rootPosition()  # 1
    def child(p): return p.h in ["1a", "1b"]
    assert [p.h for p in p.nearest_unique_roots(predicate=child)] == ["1a", "1b"]
#@+node:btheado.20191210210545.1: *3* TODO: tests to exercise uniqueness (need tree with clones)
#@-others
#@-leo
