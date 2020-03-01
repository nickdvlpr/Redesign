# -*- coding: utf-8 -*-
"""
Anki Add-on: Redesign - Progress Bar (unpublished)

Shows progress in the Reviewer in terms of passed cards per session.

Copyright:  (c) Unknown author (nest0r/Ja-Dark?) 2017
            (c) SebastienGllmt 2017 <https://github.com/SebastienGllmt/>
            (c) Glutanimate 2017 <https://glutanimate.com/>
            (c) Developer Nick 2020
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

# Do not modify the following lines
from __future__ import unicode_literals

from anki.hooks import addHook, wrap
from anki import version as anki_version

from aqt.qt import *
from aqt import mw

__version__ = '1.3.0'

############## USER CONFIGURATION START ##############

# CARD TALLY CALCULATION

# Which queues to include in the progress calculation (all True by default)
includeNew = True
includeRev = True
includeLrn = True

# Only include new cards once reviews are exhausted.
includeNewAfterRevs = False

# Limit count to your review settings as opposed to deck overall
limitToReviewSettings = True

# PROGRESS BAR APPEARANCE

showPercent = True # Show the progress text percentage or not.
showNumber = False # Show the progress text as a fraction

# Note: qwindowbg needed to be added because in original code, qbg was being applied to the background color of area surrounding the progress bar when the progress bar was not full width of screen.
qwindowbg = "#fafafa" # Background color of area surrounding progress bar
qtxt = "#2196f3" # Percentage color, if text visible.
qbg = "#eee" # Background color of progress bar.
qfg = "#2196f3" # Foreground color of progress bar.
qbr = 6 # Border radius (> 0 for rounded corners).

# optionally restricts progress bar width
maxWidth = "12px"  # (e.g. "5px". default: "")

orientationHV = Qt.Horizontal # Show bar horizontally (side to side). Use with top/bottom dockArea.
# orientationHV = Qt.Vertical # Show bar vertically (up and down). Use with right/left dockArea.

invertTF = False # If set to True, inverts and goes from right to left or top to bottom.

#dockArea = Qt.TopDockWidgetArea # Shows bar at the top. Use with horizontal orientation.
dockArea = Qt.BottomDockWidgetArea # Shows bar at the bottom. Use with horizontal orientation.
#dockArea = Qt.RightDockWidgetArea # Shows bar at right. Use with vertical orientation.
#dockArea = Qt.LeftDockWidgetArea # Shows bar at left. Use with vertical orientation.

pbStyle = "" # Stylesheet used only if blank. Else uses QPalette + theme style.
'''pbStyle options (insert a quoted word above):
    -- "plastique", "windowsxp", "windows", "windowsvista", "motif", "cde", "cleanlooks"
    -- "macintosh", "gtk", or "fusion" might also work
    -- "windowsvista" unfortunately ignores custom colors, due to animation?
    -- Some styles don't reset bar appearance fully on undo. An annoyance.
    -- Themes gallery: http://doc.qt.io/qt-4.8/gallery.html'''

##############  USER CONFIGURATION END  ##############

## Set up variables

nm = 0
failed = 0
progressBar = None
mx = 0
limitedBarLength = 0

pbdStyle = QStyleFactory.create("%s" % (pbStyle)) # Don't touch.

#Defining palette in case needed for custom colors with themes.
palette = QPalette()
palette.setColor(QPalette.Base, QColor(qwindowbg))
palette.setColor(QPalette.Highlight, QColor(qfg))
palette.setColor(QPalette.Button, QColor(qwindowbg))
palette.setColor(QPalette.WindowText, QColor(qtxt))
palette.setColor(QPalette.Window, QColor(qwindowbg))

if maxWidth:
    if orientationHV == Qt.Horizontal:
        restrictSize = "max-height: %s;" % maxWidth
    else:
        restrictSize = "max-width: %s;" % maxWidth
else:
    restrictSize = ""

try:
    # Remove that annoying separator strip if we have Night Mode, avoiding conflicts with this add-on.
    import Night_Mode
    Night_Mode.nm_css_menu \
    += Night_Mode.nm_css_menu \
    + '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    '''
except ImportError:
    failed = 1


def nmc():
    """Checks whether Night_Mode is disabled:
        if so, we remove the separator here."""
    global nm
    if not failed:
        nm = Night_Mode.nm_state_on
    if not nm:
        mw.setStyleSheet(
    '''
        QMainWindow::separator
    {
        width: 0px;
        height: 0px;
    }
    ''')


def _dock(pb):
    """Dock for the progress bar. Giving it a blank title bar,
        making sure to set focus back to the reviewer."""
    dock = QDockWidget()
    tWidget = QWidget()
    dock.setObjectName("pbDock")
    dock.setWidget(pb)
    dock.setTitleBarWidget( tWidget )

    ## Note: if there is another widget already in this dock position, we have to add ourself to the list

    # first check existing widgets
    existing_widgets = [widget for widget in mw.findChildren(QDockWidget) if mw.dockWidgetArea(widget) == dockArea]

    # then add ourselves
    mw.addDockWidget(dockArea, dock)

    # stack with any existing widgets
    if len(existing_widgets) > 0:
        mw.setDockNestingEnabled(True)

        if dockArea == Qt.TopDockWidgetArea or dockArea == Qt.BottomDockWidgetArea:
            stack_method = Qt.Vertical
        if dockArea == Qt.LeftDockWidgetArea or dockArea == Qt.RightDockWidgetArea:
            stack_method = Qt.Horizontal
        mw.splitDockWidget(existing_widgets[0], dock, stack_method)

    if qbr > 0 or pbdStyle != None:
        # Matches background for round corners.
        # Also handles background for themes' percentage text.
        mw.setPalette(palette)
    mw.web.setFocus()
    return dock


def pb():
    """Initialize and set parameters for progress bar, adding it to the dock."""
    mx = max(1, getMX())
    progressBar = QProgressBar()
    progressBar.setRange(0, mx)
    progressBar.setTextVisible(showPercent or showNumber)
    progressBar.setInvertedAppearance(invertTF)
    progressBar.setOrientation(orientationHV)
    if pbdStyle == None:
        # margin must be ≥2px on top so that the rounded corners of the progress bar don't get cutoff
        # margin on bottom for gap at bottom of screen
        # if you want percent text inside the progress bar, then need equal top and bottom margins
        progressBar.setStyleSheet(
        '''
                    QProgressBar
                {
                    text-align:center;
                    font-family: Product Sans;
                    color:%s;
                    background-color: %s;
                    border-radius: 6px;
                    margin: 15px 200px 15px 200px;
                    %s
                }
                    QProgressBar::chunk
                {
                    background-color: %s;
                    margin: 0px;
                    border-radius: 6px;
                    padding:4px;
                }
                ''' % (qtxt, qbg, restrictSize, qfg))
    else:
        progressBar.setStyle(pbdStyle)
        progressBar.setPalette(palette)
    _dock(progressBar)
    return progressBar, mx


def getMX():
    """Get deck's card counts for progress bar updates."""
    rev = nu = lrn = 0
    if includeRev:
        rev = mw.col.sched.totalRevForCurrentDeck()
    if includeLrn:
        try:
            lrn = mw.col.sched.lrnCount
        except AttributeError:
            pass
    if includeNew or (includeNewAfterRevs and rev == 0):
        nu = mw.col.sched.totalNewForCurrentDeck()
    total = rev + nu + lrn
    return total

def _getLimitedBarLength():
    """ Get a new bar length based off the number of new / lrn / rev cards you have left for the day """
    global limitedBarLength
    active_decks = mw.col.decks.active()
    if len(active_decks) > 0:
        rev = lrn = nu = 0

        # get number of cards
        for tree in [deck for deck in mw.col.sched.deckDueList() if deck[1] in active_decks]:
            if includeRev:
                rev += tree[2]
            if includeLrn:
                lrn += tree[3]
            if includeNew or (includeNewAfterRevs and rev == 0):
                nu += tree[4]

        if nu + rev < mx:
            limitedBarLength = nu+lrn+rev
            return
    limitedBarLength = -1

def _updatePB():
    """Update progress bar; hiding/showing prevents flashing bug."""
    global mx
    if progressBar:
        nmc()
        total = getMX()
        if total > mx:
            mx = total
            progressBar.setRange(0, mx)
        curr = (mx - total)
        progressBar.hide()

        barSize = mx
        if limitToReviewSettings and limitedBarLength != -1:
            barSize = limitedBarLength

            # I this can happen if the number of "rev" cards increases during the study session
            if curr > barSize:
                barSize = curr
            progressBar.setRange(0, barSize)

        if showNumber:
            if showPercent:
                percent = 100 if barSize==0 else int(100*curr/barSize)
                progressBar.setFormat("%d / %d (%d%%)" % (curr, barSize, percent))
            else:
                progressBar.setFormat("%d / %d" % (curr, barSize))
        progressBar.setValue(curr)
        progressBar.show()



def _renderBar(state, oldState):
    global mx, progressBar
    if state == "overview":
        # Set up progress bar at deck's overview page: initialize or modify.
        if not progressBar: progressBar, mx = pb()
        else: rrenderPB()
        _getLimitedBarLength()
        if showNumber:
            _updatePB()
        progressBar.show()
        nmc()
    elif state == "deckBrowser":
        # Hide the progress bar at deck list. Not deleted, so we just modify later.
        if progressBar:
            mx = 0
            progressBar.hide()


def rrenderPB():
    """Modify progress bar if it was already initialized."""
    global mx
    if getMX() >= 1:
        if mx > getMX(): _updatePB()
        else:
            mx = getMX()
            progressBar.setRange(0, mx)
            progressBar.reset()
    else: progressBar.setValue(mx)


addHook("afterStateChange", _renderBar)
addHook("showQuestion", _updatePB)


if anki_version.startswith("2.0.x"):
    """Workaround for QSS issue in EditCurrent,
    only necessary on Anki 2.0.x"""

    from aqt.editcurrent import EditCurrent

    def changeStylesheet(*args):
        mw.setStyleSheet('''
            QMainWindow::separator
        {
            width: 0px;
            height: 0px;
        }
        ''')

    def restoreStylesheet(*args):
        mw.setStyleSheet("")

    EditCurrent.__init__ = wrap(
        EditCurrent.__init__, restoreStylesheet, "after")
    EditCurrent.onReset = wrap(
        EditCurrent.onReset, changeStylesheet, "after")
    EditCurrent.onSave = wrap(
        EditCurrent.onSave, changeStylesheet, "after")
