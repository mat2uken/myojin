# -*- coding: utf-8 -*-

import os
import tempfile
from corp import app

from babel import Locale, localedata
from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po
from babel.messages.extract import extract_from_dir, DEFAULT_KEYWORDS, DEFAULT_MAPPING

__all__ = ['init_catalog', 'update_catalog', 'extract_catalog', 'compile_catalog']


LOCALES_DIRNAME = app.config['LOCALES_DIRNAME']
LOCALES_KEYWORDS = app.config['LOCALES_KEYWORDS']
MSGID_CHARSET = app.config['MSGID_CHARSET']
MSGID_BUGS_ADDRESS = app.config['MSGID_BUGS_ADDRESS']
MSGID_COPYRIGHT_HOLDER = app.config['MSGID_COPYRIGHT_HOLDER']

LOCALES_DIR = os.path.join(app.root_path, LOCALES_DIRNAME)

def _build_mo_filepath(locale, domain):
    locale_ = Locale.parse(locale)
    return os.path.join(LOCALES_DIR, locale_.language, 'LC_MESSAGES', domain + '.mo')

def _build_po_filepath(locale, domain):
    locale_ = Locale.parse(locale)
    return os.path.join(LOCALES_DIR, locale_.language, 'LC_MESSAGES', domain + '.po')

def _build_pot_filepath(domain):
    return os.path.join(LOCALES_DIR, domain + '.pot')

def extract_catalog(width=76, no_location=False, omit_header=False, sort_output=False, sort_by_file=False):
    domain = app.name
    keywords = DEFAULT_KEYWORDS.copy()
    comment_tags = {}

    from babel.messages.frontend import parse_keywords, parse_mapping
    keywords.update(parse_keywords(LOCALES_KEYWORDS))

    config_filename = os.path.join(app.root_path, 'babel.cfg')
    with open(config_filename) as f:
        method_map, options_map = parse_mapping(f)
    app.logger.debug("config: %s" % config_filename)

    from mercurial import ui, hg
    def get_latest_repo_revision():
        repo = hg.repository(ui.ui(), ".")
        latest_rev = repo.changectx("tip").rev()
        return latest_rev

    catalog = Catalog(project=domain,version=str(get_latest_repo_revision()),
                      msgid_bugs_address=MSGID_BUGS_ADDRESS, copyright_holder=MSGID_COPYRIGHT_HOLDER,
                      charset=MSGID_CHARSET)

    extract_path = os.path.join(app.root_path, '..')
    def cb(filename, method, options):
        if method == 'ignore':
            return
        filepath = os.path.normpath(os.path.join(extract_path, filename))
        optstr = ''
        if options:
            optstr = ' (%s)' % ', '.join(['%s="%s"' % (k, v) for
                                          k, v in options.items()])
        app.logger.info('extracting messages from %s%s' % (filepath, optstr))

    extracted = extract_from_dir(extract_path, method_map, options_map,
                                 keywords, comment_tags,
                                 callback=cb, strip_comment_tags=False)
    for filename, lineno, message, comments in extracted:
        filepath = os.path.normpath(os.path.join(extract_path, filename))
        catalog.add(message, None, [(filepath, lineno)], auto_comments=comments)

    output_filename = _build_pot_filepath(domain)
    with open(output_filename, 'w') as outfile:
        write_po(outfile, catalog, width=width,
                 no_location=no_location, omit_header=omit_header,
                 sort_output=sort_output, sort_by_file=sort_by_file)

def init_catalog(locale='en'):
    domain = app.name
    locale_ = Locale.parse(locale)
    output_file = _build_po_filepath(locale_.language, domain)
    input_file = _build_pot_filepath(domain)

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    with open(input_file, 'r') as infile:
        catalog = read_po(infile, locale=locale)
        catalog.locale = locale_
        catalog.fuzzy = False
    
    with open(output_file, 'w') as outfile:
        write_po(outfile, catalog)

def update_catalog(locales=None, ignore_obsolete=False, no_fuzzy_matching=False):
    domain = app.name

    po_files = []
    def add_po_file(locale):
        po_file = _build_po_filepath(locale, domain)
        if os.path.exists(po_file):
            po_files.append((locale, po_file))
    if locales is None:
        for locale in os.listdir(LOCALES_DIR):
            if os.path.isdir(os.path.join(LOCALES_DIR, locale)):
                locale_ = Locale.parse(locale)
                add_po_file(locale_.language)
    else:
        if isinstance(locales, (list, tuple)):
            for locale in locales:
                locale_ = Locale.parse(locale)
                add_po_file(locale_.language)
        else:
            locale_ = Locale.parse(locale)
            add_po_file(locale_.language)

    input_file = _build_pot_filepath(domain)
    with open(input_file, 'r') as infile:
        template = read_po(infile)
    
    for locale, filename in po_files:
        app.logger.info("updating catalog: locale(%s)" % locale)
        locale_ = Locale.parse(locale)
        with open(filename, 'U') as infile:
            catalog = read_po(infile, locale=locale_.language, domain=domain)
            catalog.update(template, no_fuzzy_matching)
            tmpname = os.path.join(os.path.dirname(filename),
                                   tempfile.gettempprefix() +
                                   os.path.basename(filename))
            with open(tmpname, 'w') as tmpfile:
                write_po(tmpfile, catalog,
                         ignore_obsolete=ignore_obsolete,
                         include_previous=False)
            
            try:
                os.rename(tmpname, filename)
            except OSError:
                os.remove(filename)
                shutil.copy(tmpname, filename)
                os.remove(tmpname)

def compile_catalog(locales=None):
    domain = app.name

    po_files = []
    mo_files = []
    def add_po_mo_file(locale):
        po_file = _build_po_filepath(locale, domain)
        if os.path.exists(po_file):
            po_files.append((locale, po_file))
            mo_file = _build_mo_filepath(locale, domain)
            mo_files.append(mo_file)
    if locales is None:
        for locale in os.listdir(LOCALES_DIR):
            if os.path.isdir(os.path.join(LOCALES_DIR, locale)):
                locale_ = Locale.parse(locale)
                add_po_mo_file(locale_.language)
    else:
        if isinstance(locales, (list, tuple)):
            for locale in locales:
                locale_ = Locale.parse(locale)
                add_po_mo_file(locale_.language)
        else:
            locale_ = Locale.parse(locales)
            add_po_mo_file(locale_.language)

    for idx, (locale, po_file) in enumerate(po_files):
        mo_file = mo_files[idx]
        with open(po_file, 'r') as infile:
            catalog = read_po(infile, locale)
            for message, errors in catalog.check():
                for error in errors:
                    app.logger.error('error: %s:%d: %s' % (po_file, message.lineno, error))

        app.logger.info('compiling catalog %r to %r' % (po_file, mo_file))
        with open(mo_file, 'w') as outfile:
            write_mo(outfile, catalog, use_fuzzy=False)
