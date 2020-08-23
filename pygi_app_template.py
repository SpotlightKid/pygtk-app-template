#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Template for a PyGTK application based on a GtkBuilder GUI file."""

from __future__ import absolute_import, print_function, unicode_literals

__all__ = [
    'MyGtkApp',
    'main',
    'parse_config'
]

# Standard library imports
import argparse
import logging
import os
import sys
import time

from os.path import abspath, dirname, expanduser, exists, join

try:
    # Python 3
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser

# Third-party packages imports
# avoid warning: "Couldn't register with accessibility bus"
os.environ['NO_AT_BRIDGE'] = '1'
from gi.repository import Gtk as gtk, GLib as glib

# construct resource paths relative to program directory
app_dir = dirname(abspath(__file__))
lib_dir = join(app_dir, 'lib')
res_dir = join(app_dir, 'res')
img_dir = join(res_dir, 'img')
ui_dir = join(res_dir, 'ui')

sys.path.insert(0, lib_dir)
# put imports from modules/packages located in ./lib here


# global constants
__app_name__ = "MyGtk3App"
__author__   = "$Author$"
__version__  = "0.1"
__date__     = "$Date$"
__usage__    = "%(prog)s [OPTIONS]"

CONFIG_FILENAME = '%s.conf' % __app_name__.lower()
GTKRC_FILENAME  = '%s.gtkrc' % __app_name__.lower()
LOG_FILENAME    = '%s.log' % __app_name__.lower()
UI_FILENAME     = '%s.ui' % __app_name__.lower()

log = logging.getLogger(__app_name__.lower())


class MyGtkApp(object):
    """GUI application class

    Takes care of creating the GUI and handling GUI events.

    """
    def __init__(self, config=None):
        """Constructor.

        Reads the GUI definition from the GtkBuilder file and creates the GUI,
        registers event handlers and starts periodic tasks to update dynamic
        GUI elements.

        """
        self.config = config

        # read UI definition from GtkBuilder XML file
        ui_file = expanduser(self.config.get('ui_file', UI_FILENAME))

        if not exists(ui_file) and exists(join(ui_dir, ui_file)):
            ui_file = join(ui_dir, ui_file)

        self.ui = gtk.Builder()
        log.debug("Loading UI definition from '%s'.", ui_file)
        self.ui.add_from_file(ui_file)
        self.window = self.ui.get_object('mainwin')
        self.window.connect("destroy", self.quit)

        self.statusbar = self.ui.get_object('statusbar')
        self.aboutdialog = self.ui.get_object('aboutdialog')
        self.aboutdialog.set_name(__app_name__)
        self.aboutdialog.set_version(__version__)
        self.aboutdialog.set_comments(
            self.aboutdialog.get_comments().replace(
                "2.x", "3.x").replace("PyGTK", "Python GObject"))

        # parse Gtk+ RC file
        rc_file = expanduser(self.config.get('rc_file', GTKRC_FILENAME))

        if not exists(rc_file) and exists(join(ui_dir, rc_file)):
            rc_file = join(ui_dir, rc_file)

        gtk.rc_parse(rc_file)

        self.init_treeview()

        # attach signal handlers
        self.ui.connect_signals(self)

        # set up periodic tasks
        glib.timeout_add(1000, self.set_time)
        self.set_time()

        self.window.set_title(__app_name__)
        self.window.show_all()

    def init_treeview(self):
        # create a TreeStore with one string column to use as the model
        self.treestore = gtk.TreeStore(str)
        self.treeview = self.ui.get_object('treeview')
        self.treeview.set_model(self.treestore)

        # we'll add some data now - 4 rows with 3 child rows each
        for parent in range(4):
            piter = self.treestore.append(None, ['parent %i' % parent])
            for child in range(3):
                self.treestore.append(piter, ['child %i of parent %i' %
                                              (child, parent)])

        # create the TreeViewColumn to display the data
        self.tvcolumn = gtk.TreeViewColumn('Column 0')

        # add tvcolumn to treeview
        self.treeview.append_column(self.tvcolumn)

        # create a CellRendererText to render the data
        self.cell = gtk.CellRendererText()

        # add the cell to the tvcolumn and allow it to expand
        self.tvcolumn.pack_start(self.cell, True)

        # set the cell "text" attribute to column 0 - retrieve text
        # from that column in treestore
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        # make it searchable
        self.treeview.set_search_column(0)

        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(0)

        # Allow drag and drop reordering of rows
        self.treeview.set_reorderable(True)

    def quit(self, widget=None, *args):
        """Quit the application."""
        gtk.main_quit()

    def on_menuitem_new_activate(self, widget, *args):
        """Handler for the "File/New" menu item."""
        pass

    def on_menuitem_open_activate(self, widget, *args):
        """Handler for the "File/Open" menu item."""
        pass

    def on_menuitem_save_activate(self, widget, *args):
        """Handler for the "File/Save" menu item."""
        pass

    def on_menuitem_save_activate(self, widget, *args):
        """Handler for the "File/Save As" menu item."""
        pass

    def on_menuitem_quit_activate(self, widget, *args):
        """Handler for the "File/Quit" menu item."""
        self.quit()

    def on_menuitem_about_activate(self, widget, *args):
        """Handler for the "Help/About..." menu item."""
        self.aboutdialog.show()

    def on_aboutdialog_response(self, widget, response):
        """Handler for the close button of the about dialog.

        Make sure you connect this handler to the GtkDialog:cancel,
        GtkDialog:response, GtkWidget:delete and GtkWidget:destroy signals
        (in the Glade properties/signals dialog of the GtkAboutDialog).

        """
        self.aboutdialog.hide()
        return True

    def set_time(self):
        """Set date and time in status bar.

        Called by a peridioc callback every second.

        The date and time display format can be set with the 'datetime_format'
        configuration setting using Python standard module 'time' placeholders
        and can contain markup valid in a GtkLabel.

        The default format is "%d.%m.%Y %H:%M:%S".

        """
        dt = time.strftime(
            self.config.get('datetime_format', "%d.%m.%Y %H:%M:%S"))
        self.set_value('timelabel', dt, markup=True)
        # return True to keep the timer running
        return True

    def set_value(self, name, value, markup=False):
        """Set text of widget with given name.

        If 'markup' is True, uses 'set_markup' method instead of 'set_text'.

        """
        widget = self.ui.get_object(name)

        if widget:
            if markup:
                widget.set_markup(value)
            else:
                widget.set_text(value)


def parse_config(filename, section="general"):
    """Read INI-style config file and return options dict of given section."""
    cfg = RawConfigParser()
    cfg.read(filename)
    if cfg.has_section(section):
        return dict(cfg.items(section))
    else:
        return {}


def setup_logging(config):
    """Configure logger instance using settings from configuration."""
    log_level = getattr(logging, config.get('log_level', 'INFO'))
    log.setLevel(log_level)
    log_filename = expanduser(config.get('log_path', LOG_FILENAME))
    log_handler = getattr(logging, config.get('log_handler') or
        'StreamHandler')(log_filename, *eval(config.get('log_args', '()')))
    log_formatter = logging.Formatter(config.get('log_fmt') or
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)


def main(args=None):
    """Main program function.

    Called with list of command line arguments (excluding program name in
    first element), can be None.

    Returns integer exit code or None.

    """
    argparser = argparse.ArgumentParser(usage=__usage__, prog=__app_name__,
        description=__doc__.splitlines()[0])
    argparser.add_argument('-V', '--version', action='version',
        version='%%(prog)s %s' % __version__)
    argparser.add_argument('-d', '--debug',
        dest="debug", action="store_true",
        help="Enable debug logging")
    argparser.add_argument('-c', '--config', dest="configpath",
        default=CONFIG_FILENAME, metavar="PATH",
        help="Path to configuration file (default: %(default)s)")

    args = argparser.parse_args(args if args is not None else sys.argv[1:])
    config = parse_config(args.configpath)
    if args.debug:
        config['log_level'] = 'DEBUG'
    setup_logging(config)

    app = MyGtkApp(config)

    try:
        gtk.main()
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
