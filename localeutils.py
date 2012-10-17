# -*- coding: utf-8 -*-

import os
import json
import tempfile
from corp import app

from babel import Locale, localedata
from babel.messages.catalog import Catalog
from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po, write_po
from babel.messages.extract import extract_from_dir, DEFAULT_KEYWORDS, DEFAULT_MAPPING

__all__ = ['init_catalog', 'update_catalog', 'extract_catalog', 'compile_catalog',
           'dump_catalog_to_json', 'save_catalog_from_json']


LOCALES_DIRNAME = app.config['LOCALES_DIRNAME']
LOCALES_KEYWORDS = app.config['LOCALES_KEYWORDS']
MSGID_CHARSET = app.config['MSGID_CHARSET']
MSGID_BUGS_ADDRESS = app.config['MSGID_BUGS_ADDRESS']
MSGID_COPYRIGHT_HOLDER = app.config['MSGID_COPYRIGHT_HOLDER']

LOCALES_DIR = os.path.join(app.root_path, LOCALES_DIRNAME)

DEFAULT_DOMAIN = app.config["DEFAULT_DOMAIN"] if app.config.get("DEFAULT_DOMAIN") else "messages"

def _build_mo_filepath(locale, domain):
    locale_ = Locale.parse(locale)
    return os.path.join(LOCALES_DIR, locale_.language, 'LC_MESSAGES', domain + '.mo')

def _build_po_filepath(locale, domain):
    locale_ = Locale.parse(locale)
    return os.path.join(LOCALES_DIR, locale_.language, 'LC_MESSAGES', domain + '.po')

def _build_pot_filepath(domain):
    return os.path.join(LOCALES_DIR, domain + '.pot')

def _get_locales(locales):
    locales_ = []
    if locales is None:
        for locale in os.listdir(LOCALES_DIR):
            if os.path.isdir(os.path.join(LOCALES_DIR, locale)):
                locale_ = Locale.parse(locale)
                locales_.append(locale_)
    else:
        if isinstance(locales, (list, tuple)):
            for locale in locales:
                locale_ = Locale.parse(locale)
                locales_.append(locale_)
        else:
            locale_ = Locale.parse(locales)
            locales_.append(locale_)
    return locales_

from mercurial import ui, hg
def _get_latest_repo_revision():
    repo = hg.repository(ui.ui(), ".")
    latest_rev = repo.changectx("tip").rev()
    return latest_rev

def extract_catalog(width=76, no_location=False, omit_header=False, sort_output=False, sort_by_file=False):
    domain = DEFAULT_DOMAIN
    keywords = DEFAULT_KEYWORDS.copy()
    comment_tags = {}

    from babel.messages.frontend import parse_keywords, parse_mapping
    keywords.update(parse_keywords(LOCALES_KEYWORDS))

    config_filename = os.path.join(app.root_path, 'babel.cfg')
    with open(config_filename) as f:
        method_map, options_map = parse_mapping(f)
    app.logger.debug("config: %s" % config_filename)

    catalog = Catalog(project=domain,version=str(_get_latest_repo_revision()),
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
        write_po(outfile, catalog, 
                 ignore_obsolete=True,
                 width=width,
                 no_location=no_location, omit_header=omit_header,
                 sort_output=sort_output, sort_by_file=sort_by_file)

def init_catalog(locale='en'):
    domain = DEFAULT_DOMAIN
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
        write_po(outfile, catalog, ignore_obsolete=False)

def dump_catalog_to_json(locale):
    domain = DEFAULT_DOMAIN
    locale_ = Locale.parse(locale)
    
    app.logger.debug("getting catalog: (%s)" % locale_.language)
    po_file = _build_po_filepath(locale_.language, domain)
    if not os.path.exists(po_file):
        raise Exception('Cannot find po_file: %s' % po_file)
    with open(po_file, 'r') as infile:
        catalog = read_po(infile, locale=locale_.language, domain=domain)

    extract_catalog()

    app.logger.debug("updating catalog: locale(%s)" % locale_.language)
    with open(_build_pot_filepath(domain), 'r') as infile:
        template = read_po(infile)
    catalog.update(template, no_fuzzy_matching=True)

    return json.dumps([[m.id, m.string,
                        ','.join(m.user_comments),
                        ','.join(["%s:%d" % loc for loc in m.locations])
                       ] for m in catalog if m.id != ''])

def save_catalog_from_json(msg_json, locale):
    domain = DEFAULT_DOMAIN
    locale_ = Locale.parse(locale)

    app.logger.info("saving catalog: locale(%s)" % locale_.language)
    catalog = Catalog(project=domain,version=str(_get_latest_repo_revision()),
                      msgid_bugs_address=MSGID_BUGS_ADDRESS, copyright_holder=MSGID_COPYRIGHT_HOLDER,
                      charset=MSGID_CHARSET)
    for key, msg_string, comments, locations in json.loads(msg_json):
        catalog.add(key, msg_string, locations=[tuple(x) for x in locations], user_comments=comments)

    app.logger.info("updateing catalog: locale(%s)" % locale_.language)
    po_file = _build_po_filepath(locale_.language, domain)
    with open(_build_pot_filepath(domain), 'r') as infile:
        template = read_po(infile)
    catalog.update(template, no_fuzzy_matching=True)
    tmpname = os.path.join(os.path.dirname(po_file),
                           tempfile.gettempprefix() +
                           os.path.basename(po_file))
    with open(tmpname, 'w') as tmpfile:
        write_po(tmpfile, catalog, ignore_obsolete=False)

    try:
        os.rename(tmpname, po_file)
    except OSError:
        os.remove(po_file)
        shutil.copy(tmpname, po_file)
        os.remove(tmpname)
    
    compile_catalog(locales=locale_.language)

def update_catalog(locales=None, ignore_obsolete=True, no_fuzzy_matching=True):
    domain = DEFAULT_DOMAIN
    locales_ = _get_locales(locales)

    po_files = []
    for locale_ in locales_:
        po_file = _build_po_filepath(locale_.language, domain)
        if os.path.exists(po_file):
            po_files.append((locale_.language, po_file))

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
    domain = DEFAULT_DOMAIN
    locales_ = _get_locales(locales)

    po_files = []
    mo_files = []
    for locale_ in locales_:
        po_file = _build_po_filepath(locale_.language, domain)
        if os.path.exists(po_file):
            po_files.append((locale_.language, po_file))
            mo_file = _build_mo_filepath(locale_.language, domain)
            mo_files.append(mo_file)

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
