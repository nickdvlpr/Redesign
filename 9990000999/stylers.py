from PyQt5.QtCore import Qt

import aqt
from anki.stats import CollectionStats
from aqt import mw, editor, QPixmap
from aqt.addcards import AddCards
from aqt.browser import Browser
from aqt.clayout import CardLayout
from aqt.editcurrent import EditCurrent
from aqt.editor import Editor
from aqt.progress import ProgressManager
from aqt.stats import DeckStats
from .gui import AddonDialog, iterate_widgets

from .config import ConfigValueGetter
from .css_class import inject_css_class
from .internals import percent_escaped, move_args_to_kwargs, from_utf8, PropertyDescriptor
from .internals import style_tag, wraps, appends_in_night_mode, replaces_in_night_mode, css
from .styles import SharedStyles, ButtonsStyle, ImageStyle, DeckStyle, LatexStyle, DialogStyle
from .internals import SnakeNameMixin, StylerMetaclass, abstract_property
from .internals import RequiringMixin




customFont = "default"; # Set your desired font here.
# Format is "Font Name With Spaces" (i.e. customFont="Times New Roman";)
# Note: If you want to change this, you need to do so in two files: styles.py and stylers.py




class Styler(RequiringMixin, SnakeNameMixin, metaclass=StylerMetaclass):

    def __init__(self, app):
        RequiringMixin.__init__(self, app)
        self.app = app
        self.config = ConfigValueGetter(app.config)
        self.original_attributes = {}

    @abstract_property
    def target(self):
        return None

    @property
    def is_active(self):
        return self.name not in self.config.disabled_stylers

    @property
    def friendly_name(self):
        name = self.name.replace('_styler', '')
        return name.replace('_', ' ').title()

    def get_or_create_original(self, key):
        if key not in self.original_attributes:
            original = getattr(self.target, key)
            self.original_attributes[key] = original
        else:
            original = self.original_attributes[key]

        return original

    def replace_attributes(self):
        try:
            for key, addition in self.additions.items():
                original = self.get_or_create_original(key)
                setattr(self.target, key, original + addition.value(self))

            for key, replacement in self.replacements.items():
                self.get_or_create_original(key)

                if isinstance(replacement, PropertyDescriptor):
                    replacement = replacement.value(self)

                setattr(self.target, key, replacement)

        except (AttributeError, TypeError):
            print('Failed to inject style to:', self.target, key, self.name)
            raise

    def restore_attributes(self):
        for key, original in self.original_attributes.items():
            setattr(self.target, key, original)




class ToolbarStyler(Styler):

    target = mw.toolbar
    require = {
        SharedStyles
    }

    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def _body(self):
        return self.shared.top




class StyleSetter:

    def __init__(self, target):
        self.target = target

    @property
    def css(self):
        return self.target.styleSheet()

    @css.setter
    def css(self, value):
        self.target.setStyleSheet(value)




class MenuStyler(Styler):
    target = StyleSetter(mw)

    # Note: this line is commented out for light mode. It affects the menus that pop up like after clicking the gear icon next to each deck on the main screen.
    # @appends_in_night_mode
    def css(self):
        return self.shared.menu




class ReviewerStyler(Styler):

    target = mw.reviewer
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps(position='around')
    def _bottomHTML(self, reviewer, _old):
        return _old(reviewer) + style_tag(percent_escaped(self.bottom_css))



    @property
    def bottom_css(self):
        return self.buttons.html + self.shared.colors_replacer + """

        /* Note: This is the reviewer screen, bottom bar, background color */
        body, #outer{
        background-color:""" + self.config.color_b + """;
        border-top-color:""" + self.config.color_b + """;
        margin: 0 95px 0 95px;
        }

        /* Note: This is the reviewer screen, bottom bar, text color of the plus signs */
        .stattxt{
            color:#bdbdbd;
        }

        /* Note: This is the reviewer screen, bottom bar, text color of text (time until next review) located above Again, Hard, Easy, etc. buttons */
        .nobold{
            color:#888;
            font-family:%s;
        }
        """ % (customFont)





class ReviewerCards(Styler):

    target = mw.reviewer
    require = {
        LatexStyle,
        ImageStyle
    }

    # TODO: it can be implemented with a nice decorator
    @wraps(position='around')
    def revHtml(self, reviewer, _old):
        return _old(reviewer) + style_tag(percent_escaped(self.body))

    @css
    def body(self):
        # Invert images and latex if needed

        css_body = """
        .card input
        {
            background-color:black!important;
            border-color:#444!important;
            color:#eee!important
        }
        .card input::selection{
            color: """ + self.config.color_t + """;
            background: #0864d4
        }
        .typeGood{
            color:black;
            background:#57a957
        }
        .typeBad{
            color:black;
            background:#c43c35
        }
        .typeMissed{
            color:black;
            background:#ccc
        }
        #answer{
            height:0;
            border:0;
            border-bottom: 2px solid #333;
            border-top: 2px solid black
        }
        img#star{
            -webkit-filter:invert(0%)!important
        }

        # This is the answer text color for cloze cards.
        # Good red color: #ef5350
        .cloze{
            color:"""+ self.config.color_p +"""!important
        }

        a{
            color:#0099CC
        }
        """

        card_color = """
        .card{
            color:""" + self.config.color_t + """!important;
        }
        """

        css = css_body + card_color + self.shared.user_color_map + self.shared.body_colors

        if self.config.invert_image:
            css += self.image.invert
        if self.config.invert_latex:
            css += self.latex.invert

        return css




class DeckBrowserStyler(Styler):

    target = mw.deckBrowser
    require = {
        SharedStyles,
        DeckStyle
    }

    @appends_in_night_mode
    def _body(self):
        styles_html = style_tag(percent_escaped(self.deck.style + self.shared.body_colors))
        return inject_css_class(True, styles_html)




class DeckBrowserBottomStyler(Styler):

    target = mw.deckBrowser.bottom
    require = {
        DeckStyle
    }

    @appends_in_night_mode
    def _centerBody(self):
        styles_html = style_tag(percent_escaped(self.deck.bottom))
        return inject_css_class(True, styles_html)




class OverviewStyler(Styler):

    target = mw.overview
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @appends_in_night_mode
    def _body(self):
        styles_html = style_tag(percent_escaped(self.css))
        return inject_css_class(True, styles_html)

    @css
    def css(self):
        return f"""
        {self.buttons.html}
        {self.shared.colors_replacer}
        {self.shared.body_colors}
        .descfont
        {{
            color: {self.config.color_t}
        }}
        """




class OverviewBottomStyler(Styler):

    target = mw.overview.bottom
    require = {
        DeckStyle
    }

    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def _centerBody(self):
        return self.deck.bottom




class AnkiWebViewStyler(Styler):

    target = mw.web
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps(position='around')
    def stdHtml(self, web, *args, **kwargs):
        old = kwargs.pop('_old')

        args, kwargs = move_args_to_kwargs(old, [web] + list(args), kwargs)

        kwargs['head'] = kwargs.get('head', '') + style_tag(self.waiting_screen)

        return old(web, *args[1:], **kwargs)

    @css
    def waiting_screen(self):
        return self.buttons.html + self.shared.body_colors




class BrowserPackageStyler(Styler):

    target = aqt.browser

    # Note: This is Browse, highlight color of starred card in list
    @replaces_in_night_mode
    def COLOUR_MARKED(self):
        return '#dedcfa'

    # Note: This is Browse, highlight color of suspended card in list
    @replaces_in_night_mode
    def COLOUR_SUSPENDED(self):
        return '#ededd5'




class BrowserStyler(Styler):

    target = Browser
    require = {
        SharedStyles,
        ButtonsStyle,
    }

    @wraps
    def init(self, browser, mw):

        if self.config.enable_in_dialogs:

            basic_css = browser.styleSheet()
            global_style = '#' + browser.form.centralwidget.objectName() + '{' + self.shared.colors + '}'
            browser.setStyleSheet(self.shared.menu + self.style + basic_css + global_style)

            browser.form.tableView.setStyleSheet(self.table)
            browser.form.tableView.horizontalHeader().setStyleSheet(self.table_header)

            browser.form.searchEdit.setStyleSheet(self.search_box)
            browser.form.searchButton.setStyleSheet(self.buttons.qt)
            browser.form.previewButton.setStyleSheet(self.buttons.qt)

    # TODO: test this
    #@wraps
    def _renderPreview(self, browser, cardChanged=False):
        if browser._previewWindow:
            self.app.take_care_of_night_class(web_object=browser._previewWeb)

    @wraps
    def buildTree(self, browser):
        root = browser.sidebarTree
        for item in root.findItems('', Qt.MatchContains | Qt.MatchRecursive):
            icon = item.icon(0)
            pixmap = icon.pixmap(32, 32)
            image = pixmap.toImage()
            image.invertPixels()
            new_icon = aqt.QIcon(QPixmap.fromImage(image))
            item.setIcon(0, new_icon)

    @wraps(position='around')
    def _cardInfoData(self, browser, _old):

        rep, cs = _old(browser)

        if self.config.enable_in_dialogs:
            rep += style_tag("""
                *
                {
                    """ + self.shared.colors + """
                }
                div
                {
                    border-color:#ff0000!important
                }
                """ + self.shared.colors_replacer + """
                """)
        return rep, cs


    # Sidebar of Browse dialog
    @css
    def style(self):
        return """
        QSplitter::handle
        {
            /* handled below as QWidget */
        }
        #""" + from_utf8("widget") + """, QTreeView
        {
            """ + self.shared.colors + """
        }
        QTreeView::item:selected:active, QTreeView::branch:selected:active
        {
            color: """ + self.config.color_t + """;
                background-color:"""+ self.config.color_p +""";
        }
        QTreeView::item:selected:!active, QTreeView::branch:selected:!active
        {
            color: """ + self.config.color_t + """;
                background-color:"""+ self.config.color_p +""";
        }
        """ + (
            """
            /* make the splitter light-dark (match all widgets as selecting with QSplitter does not work) */
            QWidget{
                background-color:"""+ self.config.color_b +""";
                color: """ + self.config.color_t + """;
            }
            /* make sure that no other important widgets - like tags box - are light-dark */
            QGroupBox{
                background-color: """ + self.config.color_b + """;
            }
            """
            if self.config.style_scroll_bars else
            ''
        )




    # Browse styles:
    # 1st (QTableView) is table of cards that can be selected.
    # 2nd (QHeaderView) is the header of the table with each column header.
    @css
    def table(self):
        return f"""
            QTableView
            {{
                margin:0px 0px 0px 0px;
                border-radius:10px;
                border:0px solid #eee;
                selection-color:#fff;
                alternate-background-color:#f8f8f8;
                gridline-color:#fff;
                {self.shared.colors};
                selection-background-color:{self.config.color_p};
                font-family:%s;
            }}
            """ % (customFont)

    # Background of header behind header text background = QHeaderView; the "color:" is for the currently sorted header's arrow
    # Header text and its background = QHeaderView::section
    @css
    def table_header(self):
        return """
            QHeaderView
            {
                background-color:#eee;
                border-radius:15px;
                color:"""+ self.config.color_p +""";
            }

            QHeaderView::section
            {
                """ + self.shared.colors + """
                        height:32px;
                        background-color:#eee;
                        border-radius:15px;
                        font-family:%s;
                        font-size:14px;
                        color:#888;
            }
            """ % (customFont)




    # Search bar = QComboBox
    # Search icon = QComboBox::down-arrow
    @css
    def search_box(self):
        return """

        QComboBox
        {
            margin:10px 0px 10px 0px;
            border:0px solid #bdbdbd;
            font-size:14px;
            font-family:"""+ customFont +""";
            border-radius:10px;
            padding:10px 10px 10px 10px;
            """ + self.shared.colors + """
        }

        QComboBox:!editable
        {
        background:#eeeeee;
        }

        QComboBox QAbstractItemView
        {
            border:0px solid #bdbdbd;
            border-radius:10px 10px 10px 10px;
            """ + self.shared.colors + """
            background:#fff
        }

        QComboBox::drop-down, QComboBox::drop-down:editable
        {
            """ + self.shared.colors + """;
            margin-right:20px;
            background:#fff;
            border:0px solid #fff;
            padding:10px 10px 10px 10px;
        }

        QComboBox::down-arrow
        {
            width:15px;
            height:15px;
            image: url('""" + self.app.icons.arrow + """')
        }
        """




# Allows styling of sidebar in Browse dialog (necessary for Anki 2.1.17 and beyond)
try:
    from aqt.browser import SidebarModel

    class SidebarModelStyler(Styler):

        target = SidebarModel

        @wraps(position='around')
        def iconFromRef(self, sidebar_model, iconRef, _old):
            icon = _old(sidebar_model, iconRef)
            if icon:
                pixmap = icon.pixmap(32, 32)
                image = pixmap.toImage()
                image.invertPixels()
                new_icon = aqt.QIcon(QPixmap.fromImage(image))
                return new_icon
            return icon
except ImportError:
    pass




class AddCardsStyler(Styler):

    target = AddCards
    require = {
        SharedStyles,
        ButtonsStyle,
    }

    @wraps
    def init(self, add_cards, mw):
        if self.config.enable_in_dialogs:

            # style add/history button
            add_cards.form.buttonBox.setStyleSheet(self.buttons.qt)

            self.set_style_to_objects_inside(add_cards.form.horizontalLayout, self.buttons.qt)

            # style the single line which has some bright color
            add_cards.form.line.setStyleSheet('#' + from_utf8('line') + '{border: 0px solid #333}')

            add_cards.form.fieldsArea.setAutoFillBackground(False)

    @staticmethod
    def set_style_to_objects_inside(layout, style):
        for widget in iterate_widgets(layout):
            widget.setStyleSheet(style)


class EditCurrentStyler(Styler):

    target = EditCurrent
    require = {
        ButtonsStyle,
    }

    @wraps
    def init(self, edit_current, mw):
        if self.config.enable_in_dialogs:
            # style close button
            edit_current.form.buttonBox.setStyleSheet(self.buttons.qt)


class ProgressStyler(Styler):

    target = None
    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle
    }

    def init(self, progress, *args, **kwargs):
        if self.config.enable_in_dialogs:
            progress.setStyleSheet(self.buttons.qt + self.dialog.style)


if hasattr(ProgressManager, 'ProgressNoCancel'):
    # before beta 31
    class LegacyProgressStyler(Styler):

        target = None
        require = {
            SharedStyles,
            DialogStyle,
            ButtonsStyle
        }

        def init(self, progress, label='', *args, **kwargs):
            if self.config.enable_in_dialogs:
                # Set label and its styles explicitly (otherwise styling does not work)
                label = aqt.QLabel(label)
                progress.setLabel(label)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet(self.dialog.style)

                progress.setStyleSheet(self.buttons.qt + self.dialog.style)

    class ProgressNoCancel(Styler):

        target = ProgressManager.ProgressNoCancel
        require = {LegacyProgressStyler}

        # so this bit is required to enable init wrapping of Qt objects
        def init(cls, label='', *args, **kwargs):
            aqt.QProgressDialog.__init__(cls, label, *args, **kwargs)

        target.__init__ = init

        @wraps
        def init(self, progress, *args, **kwargs):
            self.legacy_progress_styler.init(progress, *args, **kwargs)


    class ProgressCancelable(Styler):

        target = ProgressManager.ProgressCancellable
        require = {LegacyProgressStyler}

        @wraps
        def init(self, progress, *args, **kwargs):
            self.legacy_progress_styler.init(progress, *args, **kwargs)

else:
    # beta 31 or newer

    class ProgressDialog(Styler):

        target = ProgressManager.ProgressDialog
        require = {ProgressStyler}

        @wraps
        def init(self, progress, *args, **kwargs):
            self.progress_styler.init(progress, *args, **kwargs)


class StatsWindowStyler(Styler):

    target = DeckStats

    require = {
        DialogStyle,
        ButtonsStyle
    }

    @wraps
    def init(self, stats, *args, **kwargs):
        if self.config.enable_in_dialogs:
            stats.setStyleSheet(self.buttons.qt + self.dialog.style)


class StatsReportStyler(Styler):

    target = CollectionStats

    require = {
        SharedStyles,
        DialogStyle
    }

    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def css(self):
        return (
            self.shared.user_color_map + self.shared.body_colors + """
            body{background-image: none}
            """
        )


class EditorStyler(Styler):

    target = Editor

    require = {
        SharedStyles,
        DialogStyle,
        ButtonsStyle
    }

    # TODO: this would make more sense if we add some styling to .editor-btn
    def _addButton(self, editor, icon, command, *args, **kwargs):
        original_function = kwargs.pop('_old')
        button = original_function(editor, icon, command, *args, **kwargs)
        return button.replace('<button>', '<button class="editor-btn">')

    @wraps
    def init(self, editor, mw, widget, parentWindow, addMode=False):

        if self.config.enable_in_dialogs:

            editor_css = self.dialog.style + self.buttons.qt

            editor_css += '#' + widget.objectName() + '{' + self.shared.colors + '}'

            editor.parentWindow.setStyleSheet(editor_css)

            editor.tags.completer.popup().setStyleSheet(self.completer)

            widget.setStyleSheet(
                self.qt_mid_buttons +
                self.buttons.advanced_qt(restrict_to='#' + self.encode_class_name('fields')) +
                self.buttons.advanced_qt(restrict_to='#' + self.encode_class_name('layout'))
            )

    @staticmethod
    def encode_class_name(string):
        return "ID"+"".join(map(str, map(ord, string)))

    @css
    def completer(self):
        return f"""
            border: 1px solid #444 !important;
            color: {self.config.color_t};
            border-radius: 5px !important;
            background-color: {self.config.color_b} !important;
        """

    @css
    def qt_mid_buttons(self):
        return f"""
        QLineEdit
        {{
            {self.completer}
        }}
        """


class CardLayoutStyler(Styler):
    """Card Types modal window"""

    target = CardLayout
    require = {
          SharedStyles,
    }

    @wraps
    def init(self, card_layout, *args, **kwargs):
        if self.config.enable_in_dialogs:
            card_layout.mainArea.setStyleSheet(self.qt_style)




    # Browse>Cards (editing dialog)
    # Header text above each editor box = QGroupBox:title
    # Card code editor squares (left side of dialog) = QTextEdit; Seen when you go to Browse, then click Cards button to edit a card, and then on the left side
    @css
    def qt_style(self):
        return f"""
        QGroupBox::title
        {{
            {self.shared.colors};
        }}
        QTextEdit
        {{
            color: {self.config.color_t};
            background-color:#eee;
            border-radius:10px;
        }}
        """




class EditorWebViewStyler(Styler):

    target = editor
    require = {
        ButtonsStyle,
        ImageStyle,
        LatexStyle
    }

    # TODO: currently restart is required for this to take effect after configuration change
    # @style_tag affects the bottom half of the Browse dialog
    @appends_in_night_mode
    @style_tag
    @percent_escaped
    def _html(self):
        if self.config.enable_in_dialogs:

            custom_css = f"""
                #topbuts {self.buttons.editorButtons};

            #topbutsright button{{
                padding: inherit;
                margin-left: 1px;
            }}

            #topbuts img{{
                width:10px;
                height:10px;
                /*
                filter: invert(1);
                -webkit-filter: invert(1)
                */
            }}

            a{{
                background-color:#ffffff;
            }}

            html, body, #topbuts, .field, .fname, #topbutsOuter{{
                color: {self.config.color_t}!important;
                background: {self.config.color_b}!important;
                outline:none;
            }}
            .field {{
                border-radius: 8px;
            }}
            """

            if self.config.invert_image:
                custom_css += ".field " + self.image.invert
            if self.config.invert_latex:
                custom_css += ".field " + self.latex.invert

            return custom_css
        return ''


class AddonDialogStyler(Styler):

    target = AddonDialog
    require = {
        SharedStyles,
        ButtonsStyle
    }

    @wraps
    def init(self, window, *args, **kwargs):
        if self.config.enable_in_dialogs:
            self.style(window)

    def style(self, window):
        window.setStyleSheet(
            self.buttons.qt +
            'QDialog, QCheckBox, QLabel, QTimeEdit{' + self.shared.colors + '}'
        )
