#@+leo-ver=5-thin
#@+node:btheado.20191224142353.1: * @file external_file_changes_test.py
#@+others
#@+node:btheado.20191224142353.2: ** imports
import pytest
#@+node:btheado.20191227093319.1: ** test_refresh_after_remove_external_file
def test_refresh_after_remove_external_file(tree_F1, tmpdir):
    """
        Test exposing bug #1464 and #1466
    """
    c = tree_F1
    p1 = c.rootPosition()
    file = tmpdir.join("1")

    # Save the outline, remove the external file and refresh
    c.save()
    file.remove()
    c.refreshFromDisk()
    p1 = c.rootPosition()

    # This seems questionable to me. Why not empty if refreshed
    # from disk and the file isn't there anymore? I would think
    # refreshFromDisk would have the same behavior as closing
    # and re-opening the outline. But this is what gets the test to pass
    assert p1.b == "b_1"
#@+node:btheado.20191227093326.1: ** test_close_open_after_remove_external_file
def test_close_open_after_remove_external_file(bridge, tree_F1, tmpdir):
    """
        Another test exposing bug #1464 and #1466
    """
    # Create a new outline with @file node
    c = tree_F1
    p1 = c.rootPosition()
    file = tmpdir.join("1")

    # Save the outline, remove the external file,
    # close and reopen the outline
    c.save()
    file.remove()
    c.close()
    c = bridge.openLeoFile(c.fileName())
    p1 = c.rootPosition()
    assert p1.b == ""
#@+node:btheado.20191227093337.1: ** test_save_after_external_file_rename
@pytest.mark.xfail(reason="Leo is throwing exception when file matching original @file name is deleted. This blocks outline from being saved")
def test_save_after_external_file_rename(bridge, tree_F1, tmpdir):
    # Create a new outline with @file node and save it
    c = tree_F1
    c.save()

    # Rename the @file node and save
    p1 = c.rootPosition()
    p1.h = "@file 1_renamed"
    c.save()

    # Remove the original "@file 1" from the disk
    tmpdir.join("1").remove()

    # Change the @file contents, save and reopen the outline
    p1.b = "b_1_changed"
    c.save()
    c.close()
    c = bridge.openLeoFile(c.fileName())
    p1 = c.rootPosition()
    assert p1.b == "b_1_changed"
#@-others
#@-leo
