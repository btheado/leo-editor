#@+leo-ver=5-thin
#@+node:btheado.20191216205716.1: * @file dirty_save_test.py
#@+others
#@+node:btheado.20191216205754.1: ** imports
import pytest
#@+node:btheado.20191227093243.1: ** test_at_asis_save
def test_at_asis_save(tree_1, tmpdir):
    """
        Save and @asis file and verify contents on disk
    """
    file = tmpdir.join("test.txt")
    c = tree_1
    p1 = c.rootPosition()
    p1.h = f"@asis {str(file)}"
    c.save()
    assert file.read() == "b_1"
#@+node:btheado.20191227093251.1: ** test_at_asis_save_undo_save
def test_at_asis_save_undo_save(tree_1, tmpdir):
    """
        Duplicates the original issue reported in #1451
    """
    # change node 1 in tree_1b to have @asis
    file = tmpdir.join("test.txt")
    c = tree_1
    p1 = c.rootPosition()
    p1.h = f"@asis {str(file)}"

    # Make an undoable change to the body and save the file
    c.editCommands.upCaseWord(None)
    c.save()
    assert p1.b == "B_1"
    assert file.read() == "B_1"

    # Undo the change and save again. 
    # The changes should make it to disk
    c.undoer.undo()
    c.save()
    assert p1.b == "b_1"
    assert file.read() == "b_1"
#@-others
#@-leo
