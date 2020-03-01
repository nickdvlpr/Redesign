from .config import ConfigValueGetter
from .internals import css, snake_case, SingletonMetaclass, RequiringMixin



color_primary = '#2196f3'
customFont = "default"; # Set your desired font here.
# Format is "Font Name With Spaces" (i.e. customFont="Times New Roman";)
# Note: If you want to change this, you need to do so in three files: _init_.py, styles.py, and stylers.py




class Style(RequiringMixin, metaclass=SingletonMetaclass):

    @property
    def name(self):
        return snake_case(self.__class__.__name__).split('_')[0]

    def __init__(self, app):
        RequiringMixin.__init__(self, app)
        self.app = app
        self.config = ConfigValueGetter(app.config)


class SharedStyles(Style):

    def __init__(self, app):
        super().__init__(app)
        self.build_styles()

    def refresh(self):
        self.build_styles()

    def build_styles(self):
        # TODO
        pass

    @css
    def top(self):

        return """


        /* Note: This is Main screen, top bar, background color of full width (farthest back depth-wise) */
        body, #header{
        background-color:""" + self.config.color_b + """;
        height:40px;
        }

        /* Note: This is Main screen, top bar, curved card */
        curvedcard, #header{
        background-color:"""+ self.config.color_c +""";
        border-color:"""+ self.config.color_c +""";
        border-radius: 0 0 10px 10px;
        margin-top: 0;
        padding:0 10px 0 10px;
        width: auto;
        align: center;
        height: 35px;
        box-shadow: 0 0px 10px rgba(0, 0, 0, 0.2);
        }


        /* Note: This is Main screen, top bar, text color of buttons (color) and background color of buttons (background-color). background-color should be same as in curvedcard */
        .hitem{
        background-color:""" + self.config.color_c + """;
        color:#888;
        font-family:""" + customFont + """;
        font-weight:normal;
        padding: 0px 12px 0px 12px;
        transition: color .2s;
        }
        .hitem:hover{
        text-decoration: none;
        color:""" + self.config.color_p + """;
        }
        """




    @css
    def menu(self):
        return """
        QMenuBar,QMenu
        {
            background-color:#444!important;
            color:#eee!important
        }
        QMenuBar::item
        {
            background-color:transparent
        }
        QMenuBar::item:selected
        {
            background-color:""" + self.config.color_a + """!important;
            border-top-left-radius:6px;
            border-top-right-radius:6px
        }
        QMenu
        {
            border:1px solid #111
        }
        QMenu::item::selected
        {
            background-color:""" + self.config.color_a + """;
        }
        QMenu::item
        {
            padding:3px 25px 3px 25px;
            border:1px solid transparent
        }
        """




    @css
    def colors(self):
        return f'color: {self.config.color_t}; background-color: {self.config.color_b};'

    # Note: These are colors for Main screen (Decks), text colors of card counts for Due and New. You have to keep the first line for each, since that is the original color used by Anki, and the subsequent line of code is the color you are changing it to.
    @css
    def colors_replacer(self):
        return """
        font[color="#007700"],span[style="color:#070"]
        {
            color:#66bb6a!important
        }
        font[color="#000099"],span[style="color:#00F"]
        {
            color:#42a5f5!important
        }
        font[color="#C35617"],span[style="color:#c00"]
        {
            color:#ff7043!important
        }

        /* this color in particular is the blue for New cards remaining, seen once you click a deck and right before you start studying */
        font[color="#00a"]
        {
            color:#42a5f5
        }
        """

    @css
    def body_colors(self):
        """Generate and return CSS style of class "card"."""
        return (" body {    color:" + self.config.color_t + "!important;" +
                "background-color:" + self.config.color_b + "!important}")

    @css
    def user_color_map(self):
        style = ''
        for old, new in self.config.user_color_map.items():
            if old and new:
                style += f'font[color="{old}"]{{color: {new}!important}}'
        return style




class ButtonsStyle(Style):

    idle = """
        color:#888;
        margin-top:0;
        position:relative;
        top:0;
        padding: 8px 16px 8px 16px;
        transition: color .2s, background-color .2s, border-color .2s, padding .4s;
    """
    hover = 'background-color:%s; color: #fff; border-color:%s; padding: 8px 20px 8px 20px;' %(color_primary, color_primary)
    active = 'color: #fff;'


    @css
    def qt(self):
        return self.advanced_qt() + (self.qt_scrollbars if self.config.style_scroll_bars else '')

    # Note: This is the Browse button style
    # First is idle state. Second is hover. Third is clicked.
    def advanced_qt(self, restrict_to_parent='', restrict_to=''):
        return """
        """ + restrict_to_parent + """ QPushButton""" + restrict_to + """
        {
            background-color: """+ self.config.color_c +""";
            border-radius:15px;
            border: 1px solid #bdbdbd;
            padding: 8px 16px 8px 16px;
            """ + self.idle + """
        }
        """ + restrict_to_parent + """ QPushButton""" + restrict_to + """:hover
        {
            """ + self.hover + """
                background-color:"""+ self.config.color_p +"""; padding: 8px 16px 8px 16px;
        }
        """

        + restrict_to_parent + """ QPushButton""" + restrict_to + """:pressed
        {
            """ + self.active + """
                background-color:"""+ self.config.color_p +""";
        }
        """

        + restrict_to_parent + """ QPushButton""" + restrict_to + """:disabled
        {
            """ + self.active + """
                background-color:"""+ self.config.color_b +""";
        }
        """ + restrict_to_parent + """ QPushButton""" + restrict_to + """:focus
        {
            outline: 1px dotted #4a90d9;
        }
        """




    # Scrollbar colors are only used if "Dark scrollbars" is enabled
    scrollbar_size = 15
    scrollbar_background = '{self.config.color_b}'
    scrollbar_color = '#eeeeee'

    # Scrollbar style for Browse window table and other dialogs
    @css
    def qt_scrollbars(self):
        return f"""
        QScrollBar:horizontal, QScrollBar:vertical {{
            background: {self.scrollbar_background};
        }}
        QScrollBar:add-page, QScrollBar:sub-page{{
            background: {self.scrollbar_background};
        }}
        QScrollBar::handle:horizontal, QScrollBar::handle:vertical {{
            background: {self.scrollbar_color};
        }}
        QScrollBar {{
            margin: 0
        }}
        QScrollBar:vertical {{
            width: {self.scrollbar_size}px;
        }}
        QScrollBar:horizontal {{
            height: {self.scrollbar_size}px;
        }}
        QScrollBar::handle {{
            margin: 4px 0 0 4px;
            border-radius: 5px
        }}
        QScrollBar::handle:vertical {{
            min-height: 20px;
        }}
        QScrollBar::handle:horizontal {{
            min-width: 20px;
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}
        QScrollBar:left-arrow, QScrollBar::right-arrow, QScrollBar:up-arrow, QScrollBar::down-arrow {{
            border: none;
            background: none;
            color: none
        }}
        """

    # Scrollbar style for main Decks page
    @css
    def scrollbars(self):
        return f"""
        ::-webkit-scrollbar{{
            width: {self.scrollbar_size - 8}px;
        }}
        ::-webkit-scrollbar:horizontal {{
            height: {self.scrollbar_size - 8}px;
        }}
        ::-webkit-scrollbar-track {{
            background: {self.scrollbar_background};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {self.scrollbar_color};
            border-radius: 20px;
        }}
        """

    @css
    def html(self):
        return f"""
        button
        {{
            { self.idle }
            background:{self.config.color_c};
            border:0px {self.config.color_c};
            margin: 8px;
            border-radius: 40px;
            font-family:%s;
            outline: none;
            box-shadow: 0 0px 10px rgba(0, 0, 0, 0.2);
        }}
        button:hover
        {{
            { self.hover }
            background-color:{self.config.color_p};
            border-color:{self.config.color_p};
        }}
        button:active
        {{
            { self.active }
            background:{self.config.color_p};
        }}
            """ %(customFont) + (self.scrollbars if self.config.style_scroll_bars else '')



    # Button style for Editor portion (bottom half) of Browse window. This style surrounds the bold, italics, etc. buttons.
    @css
    def editorButtons(self):
        return f"""
            button{{
                { self.idle }
                width:auto;
                height:auto;
                background:{self.config.color_c};
                border:1px solid #bdbdbd;
                margin:2px;
                padding: 4px 8px 4px 8px;
                border-radius: 40px;
                font-family:%s;
                outline: none;
            }}
            """ % (customFont)






class DeckStyle(Style):
    require = {
        SharedStyles,
        ButtonsStyle
    }


    @css
    def bottom(self):
        return self.buttons.html + """
        #header
        {
            color:#000!important;
            background:""" + self.config.color_b + """;
            border-top-color:""" + self.config.color_b + """;
            height:40px
        }
        """


    # Note: This is Main screen (Decks) styling of the text and everything.
    # Look at GitHub web/deckbrowser.css for other things to style.
    @css
    def style(self):
        return self.buttons.html + self.shared.colors_replacer + """
        a {
            color:#0099CC;
            font-family:""" + customFont + """;
        }

        a.deck {
            text-transform: none;
            font-size: 15px;
            color:#212121;
            background-color:""" + self.config.color_b + """;
            border-radius: 50px;
            font-family:""" + customFont + """;
            padding:6px 12px 6px 12px;
            transition: color .1s, background-color .1s, padding .4s;
        }
        a.deck:hover {
            text-decoration: none;
            color:#fff;
            background-color:""" + self.config.color_p + """;
            border-radius: 50px;
            border-color:""" + self.config.color_p + """;
            width: auto;
            height: auto;
            padding:6px 16px 6px 16px;
        }

        tr.deck td{
            height:35px;
            border-bottom-color:""" + self.config.color_b + """;
            font-family:""" + customFont + """;
            border-radius: 50px;
        }
        tr.deck font[color="#007700"]{
            color:#00CC00;
            font-family:""" + customFont + """;
        }
        tr.deck font[color="#000099"]{
            color:#00BBFF;
            font-family:""" + customFont + """;
        }
        tr.deck{
            height:35px;
            font-family:""" + customFont + """;
        }

        /* the plus or minus sign for collapsing decks */
        .collapse{
            color:#212121;
            font-family:""" + customFont + """;
            padding-right: 8px;
        }



        /* text at top saying Deck, Due, and New, this does the font family */
        /* Note: changes here also affect the deck names text too, so you have to add the same properties to a.deck (above) */
        tr {
            color:#bdbdbd;
            font-family:""" + customFont + """;
            text-transform: uppercase;
            font-size: 13px;
        }


        .decktd {
            text-decoration: none;
            border-radius: 50px;
        }

        /* highlight of currently selected deck in list */
        .current {
            text-decoration: none;
            background-color:""" + self.config.color_b + """;
            border-radius: 50px;
        }

        .filtered{
            color:#00AAEE!important
            font-family:""" + customFont + """;
        }



        .gears{
            padding-left:32px;
            padding-right:16px;
            width: 1em;
            height: 1em;
            opacity: .5;
        }

        """




class MessageBoxStyle(Style):

    require = {
        ButtonsStyle
    }

    @css
    def style(self):
        """
        Generate and return CSS style of class QMessageBox,
        using global color declarations
        """
        return f"""
        QMessageBox,QLabel
        {{
            color: { self.config.color_t };
            background-color: { self.config.color_b };
            font-family:%s;
        }}
        { self.buttons.qt }
        QPushButton
        {{
            min-width: 70px
        }}
        """ % (customFont)


class ImageStyle(Style):

    @css
    def invert(self):
        return """
        img
        {
            filter:invert(1);
            -webkit-filter:invert(1)
        }
        """


class LatexStyle(Style):

    @css
    def invert(self):
        return """
        .latex
        {
            filter:invert(1);
            -webkit-filter:invert(1)
        }
        """


class DialogStyle(Style):

    require = {
        SharedStyles,
        ButtonsStyle
    }

    @css
    def style(self):
        return """
            QDialog,QLabel,QListWidget,QFontComboBox,QCheckBox,QSpinBox,QRadioButton,QHBoxLayout
            {
            """ + self.shared.colors + """
            }
            QFontComboBox::drop-down{border: 0px; border-left: 1px solid #555; width: 30px;}
            QFontComboBox::down-arrow{width:12px; height:8px;
                top:1px;
                image:url('""" + self.app.icons.arrow + """')
            }
            QFontComboBox, QSpinBox{border: 1px solid #555}

            QTabWidget QWidget
            {
                color:""" + self.config.color_t + """;
                background-color:#222;
                border-color:#555
            }
            QTabWidget QLabel {
                position:relative
            }
            QTabWidget QTabBar
            {
                color:#000
            }
            QTabWidget QTextEdit
            {
                border-color:#555
            }
            QTabWidget QGroupBox::title
            {
                subcontrol-origin: margin;
                subcontrol-position:top left;
                margin-top:-7px
            }
            """ + self.buttons.advanced_qt("QTabWidget")
