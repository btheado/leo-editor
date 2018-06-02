"""
dock_layout - use QDockWidgets to layout Leo panes.

## Implementation notes

dock_layout puts all Leo panes into QDockWidgets. All docks are placed
in a single dock area, and the QMainWindow's main widget is not used.
Nested docking is enabled, allowing almost any layout to be created. The
Minibuffer is moved to the toolbar.

Qt provides save/restoreState and save/restoreGeometry methods on
QMainWindow. I'm not really sure how they work, simple trials haven't
shown them working as expected. I'm not sure how they could possible
restore the complex state Leo might want restored, where a pane could
hold anything from an image to an authenticated connection to a remote
service. However they work, they generate opaque binary blobs. Docs. are
not extensive.

So dock_layout uses it's own persistence mechanism.  All docks are top
level children of the QMainWindow, despite their hierarchical arrangement.
However it's necessary to create them in a particular order to recreate a
particular layout.  to_json() save alls the rectangles of visible docks,
and tabbing grouping of non-visible docks, without hierarchy.  load_json()
reconstructs the hierarchy, and hence the order in which docks must be
created during restoration of a layout, as follows:

 - a list of all docks with rectangles
 - find the maximum bounding box (bbox) of all docks
 - for each dock, find the proportion, 0-1, of the full bbox spanned by the
   dock, both width and height, note the greater of the two, and its
   orientation.  E.g. (0.7, horiz), or (1.0, vert).
 - There will always be at least one splitter that spans the whole bbox (proportion
   1.0), you can't arrange splitters so that that's not true.
 - There may be more than one, that's ok
 - Pick one of the splitters that spans the whole bbox.  It will split the bbox
   into 1-3 pieces:
       - 1 - this dock is the last widget left to place
       - 2 - this dock spans the top/bottom/left/right edge of the bbox
       - 3 - this dock spans the middle of the bbox horizontally or
             vertically.
 - So processing this dock creates 0-2 new bbox regions to process, place
   on a todo list.

"""
import json
import os

from collections import defaultdict, namedtuple

import leo.core.leoGlobals as g
from leo.core.leoQt import QtCore, QtWidgets, QtGui
QtConst = QtCore.Qt

DockAreas = (
    QtConst.TopDockWidgetArea, QtConst.BottomDockWidgetArea,
    QtConst.LeftDockWidgetArea, QtConst.RightDockWidgetArea
)

WID_ATTR = '_tm_id'

BBox = namedtuple('BBox', 'minx miny maxx maxy')

def init():
    '''Return True if the plugin has loaded successfully.'''
    if g.app.gui.guiName() != "qt":
        print('dock_layout.py plugin not loading because gui is not Qt')
        return False
    g.registerHandler('after-create-leo-frame', onCreate)
    g.plugin_signon(__name__)
    create_commands()
    return True
def onCreate (tag, key):
    c = key.get('c')
    DockManager(c)
    ToolManager(c)
def create_commands():
    """create_commands - add commands"""
    cmds = [
        'dockify', 'load_json', 'load_layout', 'save_layout', 'toggle_titles',
        'open_dock_menu', 'plot_json',
    ]
    for cmd_name in cmds:
        def cmd(event, cmd_name=cmd_name):
            getattr(event['c']._dock_manager, cmd_name)()
        g.command("dock-%s" % cmd_name.replace('_', '-'))(cmd)

@g.command('dock-json')
def dock_json(event=None):
    """dock_json - introspect dock layout

    Args:
        event: Leo command event
    """
    json.dump(
        event['c']._dock_manager.to_json(),
        open(g.os_path_join(g.computeHomeDir(), 'dock.json'), 'w'),
        indent=4,
        sort_keys=True
    )
def wid(w, value=None):
    """wid - get/set widget ID

    Args:
        w: widget
        value (str): value to set
    Returns:
        str: widget id
    """
    if value is None:
        return getattr(w, WID_ATTR, None)
    else:
        setattr(w, WID_ATTR, value)
class DockManager(object):
    """DockManager - manage QDockWidget layouts"""

    def __init__(self, c):
        """bind to Leo context

    Args:
        c (context): Leo outline
        """
        self.c = c
        c._dock_manager = self

        # set _tm_id where needed, previously done in free_layout
        wid(c.frame.top.findChild(QtWidgets.QWidget, "outlineFrame"), '_leo_pane:outlineFrame')
        wid(c.frame.top.findChild(QtWidgets.QWidget, "logFrame"), '_leo_pane:logFrame')
        wid(c.frame.top.findChild(QtWidgets.QWidget, "bodyFrame"), '_leo_pane:bodyFrame')

        def load(timer, self=self):
            timer.stop()
            self.load()
        timer = g.IdleTime(load, delay=1000)
        timer.start()
    @staticmethod
    def area_span(widget, bbox):
        """area_span - find max. proportion of area width/height spanned
        by widget

        Args:
            widget ({attr}): widget attributes
            bbox (tuple): xmin, ymin, xmax, ymax
        Returns:
            tuple: (float, bool) max. proportion, is width
        """
        xprop = widget['width'] / float(bbox.maxx - bbox.minx)
        yprop = widget['height'] / float(bbox.maxy - bbox.miny)
        if xprop > yprop:
            return xprop, True
        else:
            return yprop, False

    @staticmethod
    def bbox(widgets):
        """bbox - get max extent of list of widgets

        Args:
            widgets ([{attr}]): list of dicts of widget's attributes
        Returns:
            tuple: xmin, ymin, xmax, ymax
        """
        x = []
        y = []
        for w in [i for i in widgets if i['visible']]:
            x.append(w['x'])
            x.append(w['x']+w['width'])
            y.append(w['y'])
            y.append(w['y']+w['height'])
        return BBox(minx=min(x), miny=min(y), maxx=max(x), maxy=max(y))
    def dockify(self):
        """dockify - Move UI elements into docks"""
        c = self.c
        mw = c.frame.top
        childs = []
        splits = (QtWidgets.QSplitter, QtWidgets.QSplitterHandle)
        for splitter in c.frame.top.centralWidget().findChildren(QtWidgets.QSplitter):
            for child in splitter.children():
                if isinstance(child, splits):
                    continue
                if not isinstance(child, QtWidgets.QWidget):
                    continue  # have seen QActions
                childs.append(child)

        for child in childs:
            w = QtWidgets.QDockWidget(child.objectName(), mw)
            w.setWidget(child)
            mw.addDockWidget(QtConst.TopDockWidgetArea, w)

        tb = QtWidgets.QToolBar()
        mw.addToolBar(QtConst.BottomToolBarArea, tb)
        tb.addWidget(c.frame.miniBufferWidget.widget.parent())

        mw.centralWidget().close()

        for child in mw.findChildren(QtWidgets.QDockWidget):
            if child.windowTitle() == 'logFrame':
                log_dock = child
                break
        else:
            raise Exception("Can't find logFrame")

        tw = c.frame.log.tabWidget
        while tw.count() > 1:
            dw = QtWidgets.QDockWidget(tw.tabText(1), mw)
            w = tw.widget(1)
            if not wid(w):
                wid(w, '_leo_tab:%s' % tw.tabText(1))
            dw.setWidget(w)
            mw.tabifyDockWidget(log_dock, dw)

    def find_dock(self, id_):
        """find_dock - find a dock widget

        Args:
            ns_id (str): the ID for the widget
        Returns:
            QWidget: the widget
        """
        for child in self.c.frame.top.findChildren(QtWidgets.QDockWidget):
            if wid(child.widget()) == id_:
                return child
        w = self.c._tool_manager.provide(id_)
        if w:
            dock = QtWidgets.QDockWidget()# self.c.frame.top)
            dock.setWidget(w)
            return dock
        g.log("Didn't find %s" % id_, color='warning')
    @staticmethod
    def in_bbox(widget, bbox):
        """in_bbox - determine if the widget's in a bbox

        Args:
            widget ({attr}): widget attributes
            bbox (tuple): xmin, ymin, xmax, ymax
        Returns:
            bool: widget is in bbox
        """
        xctr = widget['x']+widget['width']/2
        yctr = widget['y']+widget['height']/2
        return bbox.minx < xctr < bbox.maxx and bbox.miny < yctr < bbox.maxy

    def load(self):
        """load - load layout on idle after load"""
        self.dockify()
        def delayed_layout(timer, self=self):
            timer.stop()
            self.load_json(g.os_path_finalize_join(
                g.computeHomeDir(), '.leo', 'layouts', 'default.json'))
        timer = g.IdleTime(delayed_layout, delay=1000)
        timer.start()

    def load_json(self, file):
        """load_json - load layout from JSON file

        Args:
            file: JSON file to load
        """
        D = True
        if D:
            _names = lambda x: ' '.join(i['_tm_id'] for i in x)
        c = self.c
        d = json.load(open(file))

        # make sure nothing's tabbed
        for w in c.frame.top.findChildren(QtWidgets.QDockWidget):
            c.frame.top.addDockWidget(QtConst.TopDockWidgetArea, w)

        widgets = list(d['widget'].values())
        todo = [(widgets, self.bbox(widgets), None, None)]

        Span = namedtuple('Span', "start size")  # x, width or y, height
        while todo:
            widgets, bbox, ref, align = todo.pop(0)

            # look for columns and rows
            cols = defaultdict(lambda: list())
            rows = defaultdict(lambda: list())
            for w in widgets:
                if not w['visible']:
                    continue
                cols[Span(w['x'], w['width'])].append(w)
                rows[Span(w['y'], w['height'])].append(w)
            heights = {k:sum(w['height'] for w in cols[k]) for k in cols}
            widths = {k:sum(w['width'] for w in rows[k]) for k in rows}
            height = -(bbox.miny - bbox.maxy)
            width = bbox.maxx - bbox.minx
            """
            if the maximum width of all rows is the width of a column, column split
            if the maximum height of all columns is the height of a row, row split
            """
            if D:
                print(height, width)
                print(heights)
                print(widths)

            PropSpan = namedtuple('PropSpan', 'prop span')
            col_prop = sorted([PropSpan(heights[i]/float(height), i) for i in heights], reverse=True)
            row_prop = sorted([PropSpan(widths[i]/float(width), i) for i in widths], reverse=True)

            #X ordered = sorted(
            #X     widgets,
            #X     key=lambda x: self.area_span(x, bbox),
            #X     reverse=True
            #X )
            #X if D:
            #X     for i in widgets:
            #X         print(i, self.area_span(i, bbox))
            #X first = ordered[0]
            if row_prop[0].prop > col_prop[0].prop:  # width spanning
                below = BBox(bbox.minx, bbox.miny, bbox.maxx, row_prop[0].span.start)
                above = BBox(bbox.minx, row_prop[0].span.start+row_prop[0].span.size, bbox.maxx, bbox.maxy)
                within = BBox(bbox.minx, row_prop[0].span.start, bbox.maxx, row_prop[0].span.start+row_prop[0].span.size)
                in_below = [i for i in widgets if i['visible'] and self.in_bbox(i, below)]
                in_above = [i for i in widgets if i['visible'] and self.in_bbox(i, above)]
                in_within = [i for i in widgets if i['visible'] and self.in_bbox(i, within)]
                if D:
                    print("below", below, in_below)
                    print("above", above, in_above)
                    print("within", within, in_within)
                first = in_within[0]
                if D:
                    print("%s over %s" % (_names(in_above), _names(in_below)))

                if ref:
                    ref_w = self.find_dock(ref)
                    nxt_w = self.find_dock(first[WID_ATTR])
                    if not ref_w or not nxt_w:
                        break  # aborts loading layout

                    if align == QtConst.Vertical:
                        if d['widget'][ref]['y'] > first['y']:
                            self.swap_dock(ref_w, nxt_w)
                    else:
                        if d['widget'][ref]['x'] > first['x']:
                            self.swap_dock(ref_w, nxt_w)

                    c.frame.top.splitDockWidget(ref_w, nxt_w, align)

                if in_below:
                    todo.append((in_below, below, first[WID_ATTR], QtConst.Vertical))
                if in_above:
                    todo.append((in_above, above, first[WID_ATTR], QtConst.Vertical))
            else:  # height spanning
                left = BBox(bbox.minx, bbox.miny, col_prop[0].span.start, bbox.maxy)
                right = BBox(col_prop[0].span.start+col_prop[0].span.size, bbox.miny, bbox.maxx, bbox.maxy)
                within = BBox(col_prop[0].span.start, bbox.miny, col_prop[0].span.start+col_prop[0].span.size, bbox.maxy)
                in_left = [i for i in widgets if i['visible'] and self.in_bbox(i, left)]
                in_right = [i for i in widgets if i['visible'] and self.in_bbox(i, right)]
                in_within = [i for i in widgets if i['visible'] and self.in_bbox(i, within)]
                if D:
                    print("left", left, in_left)
                    print("right", right, in_right)
                    print("within", within, in_within)
                first = in_within[0]
                if D:
                    print("%s left of %s" % (_names(in_left), _names(in_right)))

                if ref:
                    ref_w = self.find_dock(ref)
                    nxt_w = self.find_dock(first[WID_ATTR])
                    if not ref_w or not nxt_w:
                        break  # aborts loading layout

                    if align == QtConst.Vertical:
                        if d['widget'][ref]['y'] > first['y']:
                            self.swap_dock(ref_w, nxt_w)
                    else:
                        if d['widget'][ref]['x'] > first['x']:
                            self.swap_dock(ref_w, nxt_w)

                    c.frame.top.splitDockWidget(ref_w, nxt_w, align)

                if in_left:
                    todo.append((in_left, left, first[WID_ATTR], QtConst.Horizontal))
                if in_right:
                    todo.append((in_right, right, first[WID_ATTR], QtConst.Horizontal))

        # for each tab group, find the visible tab, and and place other
        # docks on it
        for tg in d['tab_group'].values():
            # find the visible tab, which is already placed
            for viz_n, viz in enumerate(tg):
                if d['widget'][viz]['visible']:
                    break
            else:
                g.log("Can't find visible tab for "+str(tg))
                continue
            viz_w = self.find_dock(viz)
            if not viz_w:
                break  # aborts loading layout

            # make a list of tabs, left to right
            ordered = [viz_w]
            for tab in tg:  # add other tabs to group
                if tab == viz:
                    continue
                tab_w = self.find_dock(tab)
                if not tab_w:
                    break
                c.frame.top.tabifyDockWidget(viz_w, tab_w)
                ordered.append(tab_w)
            for n in range(len(tg)):  # reorder tabs to match list
                src = self.find_dock(tg[n])
                if not src:
                    break
                self.swap_dock(src, ordered[n])
            self.find_dock(viz).raise_()  # raise viz. tab

        if hasattr(c.frame.top, 'resizeDocks'):  # not in Qt 4?
            widgets = sorted(
                list(d['widget'].values()),
                key=lambda x: self.area_span(x, bbox),
                reverse=True
            )
            docks = [self.find_dock(i[WID_ATTR]) for i in widgets if i['visible']]
            heights = [i['height'] for i in widgets if i['visible']]
            c.frame.top.resizeDocks(docks, heights, QtConst.Vertical)
            widths = [i['width'] for i in widgets if i['visible']]
            c.frame.top.resizeDocks(docks, widths, QtConst.Horizontal)
    def load_layout(self):
        """load_layout - load a layout"""
        layouts = g.os_path_finalize_join(g.computeHomeDir(), '.leo', 'layouts')
        if not g.os_path_exists(layouts):
            os.makedirs(layouts)
        file = g.app.gui.runOpenFileDialog(self.c, "Pick a layout",
            [("Layout files", '*.json'), ("All files", '*')], startpath=layouts)
        if file:
            self.load_json(file)
    def open_dock_menu(self, pos=None):
        """open_dock_menu - open a dock"""
        menu = QtWidgets.QMenu(self.c.frame.top)

        for id_, name in self.c._tool_manager.tools():
            act = QtWidgets.QAction(name, menu)
            act.triggered.connect(lambda checked, id_=id_, name=name: self.open_dock(id_, name))
            menu.addAction(act)
        menu.exec_(QtGui.QCursor.pos())
    def open_dock(self, id_, name):
        """open_dock - open a dock

        Args:
            id_ (str): dock ID
        """
        w = self.c._tool_manager.provide(id_)
        if w:
            wid(w, id_)
            main_window = self.c.frame.top
            new_dock = QtWidgets.QDockWidget(name, main_window)
            new_dock.setWidget(w)
            main_window.addDockWidget(QtConst.TopDockWidgetArea, new_dock)
        else:
            g.log("Could not find tool: %s" % id_, color='error')
    def save_layout(self):
        """save_layout - save a layout"""
        # FIXME: startpath option here?  cwd doesn't work
        layouts = g.os_path_finalize_join(g.computeHomeDir(), '.leo', 'layouts')
        if not g.os_path_exists(layouts):
            os.makedirs(layouts)
        old_cwd = os.getcwd()
        os.chdir(layouts)
        file = g.app.gui.runSaveFileDialog(self.c, title="Save a layout",
            filetypes=[("Layout files", '*.json'), ("All files", '*')],
            initialfile=layouts)
        os.chdir(old_cwd)
        if file:
            with open(file, 'w') as out:
                json.dump(self.to_json(), out)
    @staticmethod
    def swap_dock(a, b):
        """swap_dock - swap contents / titles of a pair of dock widgets

        Args:
            a (QDockWidget): widget a
            b (QDockWidget): widget b
        """
        w = a.widget()
        a_txt = a.windowTitle()
        a.setWidget(b.widget())
        a.setWindowTitle(b.windowTitle())
        b.setWidget(w)
        b.setWindowTitle(a_txt)
    def to_json(self):
        """to_json - introspect dock layout

        Returns:
            dict: 'json' rep. of layout
        """

        c = self.c
        _id = lambda x: wid(x.widget())

        ans = {'area': {}, 'widget': {}, 'tab_group': {}}
        widgets = c.frame.top.findChildren(QtWidgets.QDockWidget)
        tab_known = set()  # widgets with known tab status
        tab_group = 0
        for w in widgets:
            area = c.frame.top.dockWidgetArea(w)
            ans['area'].setdefault(area, []).append(_id(w))
            # dict for w, maybe already added by tabbed_with code
            d = ans['widget'].setdefault(_id(w), {})
            d['area'] = area
            # https://stackoverflow.com/a/22238571/1072212
            # test for tabs being visible
            d['visible'] = not w.visibleRegion().isEmpty()
            if w not in tab_known:  # see if widget is in a tab group
                tabbed_with = c.frame.top.tabifiedDockWidgets(w)
                if tabbed_with:
                    assert w not in tabbed_with
                    tabbed_with.append(w)  # include widget in group, this seems to
                                           # preserve tab order, but feels fragile
                    tab_group += 1
                    ans['tab_group'][tab_group] = [_id(i) for i in tabbed_with]
                    for tw in tabbed_with:  # assign group ID to all members
                        tab_known.add(tw)
                        ans['widget'].setdefault(_id(tw), {})['tab_group'] = tab_group
                else:
                    d['tab_group'] = None
            for i in 'x', 'y', 'width', 'height':
                d[i] = getattr(w, i)()
            d[WID_ATTR] = _id(w)
        return ans


    def toggle_titles(self):
        c = self.c
        mw = c.frame.top
        # find the first QDockWidget and see if titles are hidden
        if mw.findChild(QtWidgets.QDockWidget).titleBarWidget() is None:
            # default, not hidden, so hide with blank widget
            widget_factory = lambda: QtWidgets.QWidget()
        else:
            # hidden, so revert to default, not hidden
            widget_factory = lambda: None
        # apply to all QDockWidgets
        for child in mw.findChildren(QtWidgets.QDockWidget):
            child.setTitleBarWidget(widget_factory())

class ToolManager(object):
    """ToolManager - manage tools (panes, widgets)

    Things that provide widgets should do:

        c.user_dict.setdefault('_tool_providers', []).append(provider)

    which avoids dependence of this class being inited.

    provider should be an object with callables as follows:

        provider.tm_provides() - a list of (id_, name) tuples, ids and names of
        things this provider can provide

        provider.tm_provide(id_, state) - provide a QWidget based on ID, which
        will be initialized with dict state

        provider.tm_save_state(w) - provide a JSON serialisable dict that saves
        state for widget w

    NOTE: providers are only asked to provide things they've already claimed
    (tm_provides()) they provide, unline NestedSplitter which asked all
    providers in turn to provide a widget. So providers /no longer/ need to
    check what they're being asked for, unless they provide more than one thing.

    Example:

        class LeoEditPane:
            def tm_provides(): return [('_lep', "Leo Edit Pane")]
            def tm_provide(id_, state):
                assert id_ == '_lep'
                return self.make_editpane(state)
                # e.g. if 'UNL' in state, select that node
            def tm_save_state(w):
                assert w._tm_id == '_lep'
                return self.save_state(w)
                # e.g. {'UNL': self.c.vnode2position(w.v).get_UNL()}
    """

    def __init__(self, c):
        """bind to c"""
        self.c = c
        self.providers = c.user_dict.setdefault('_tool_providers', [])
        c._tool_manager = self

    def tools(self):
        """tools - list available tools"""
        ans = []
        for provider in self.providers:
            ans.extend(provider.tm_provides())
        return ans

    def provide(self, id_, state=None):
        if state is None:
            state = {}
        for provider in self.providers:
            ids = [i[0] for i in provider.tm_provides()]
            if id_ in ids:
                w = provider.tm_provide(id_, state)
                if w:
                    wid(w, id_)
                    g.log("Provided %s" % id_)
                    return w
        g.log("Couldn't provide %s" % id_, color='warning')