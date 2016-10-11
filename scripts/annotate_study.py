#!/usr/bin/env python

"""
Create a map-annotation on a top-level object based on an IDR study file.
All fields are treated as optional
Example:

    scripts/annotate_study.py \
        idr-metadata/idr0001-graml-sysgro/idr0001-study.txt Screen:3
"""

import argparse
import csv

from pyidr.mapannotations import create_map_annotation
# This import needs to come after the above, otherwise there's a mysterious
# "ImportError: cannot import name NamedValue" error
from omero.cli import CLI, ProxyStringType


# Mapping of
# - study keys (from the study file)
# - displayed names
# - displayed values (default value)
study_keys = [
    ('Study PubMed ID', 'PubMed ID'),
    ('Study PubMed ID', 'PubMed ID URL',
     'http://www.ncbi.nlm.nih.gov/pubmed/{{ value }}'),
    ('Study DOI', 'Publication DOI'),
    ('Study DOI', 'Publication DOI URL', 'http://dx.doi.org/{{ value }}'),
    ('Study Publication Title', 'Title'),
    ('Study Author List', 'Authors'),
    ('Study External URL', 'External URL'),
]

ns = 'openmicroscopy.org/idr/study'


def get_pairs(study):
    table = csv.reader(study, delimiter='\t')

    kvpairs = []
    for row in table:
        for items in study_keys:
            key = items[0]
            display = items[1]
            try:
                template = items[2]
            except IndexError:
                template = '{{ value }}'

            # All keys are optional, duplicates allowed, omit empty value
            if len(row) > 1 and row[0] == key:
                value = template.replace('{{ value }}', row[1])
                kvpairs.append((display, value))

    return kvpairs


def run(studyfile, targetstr):
    try:
        # `omero shell --login` automatically creates the client object
        session = client.getSession()
        cli = None
    except NameError:
        cli = CLI()
        cli.loadplugins()
        cli.onecmd('login')
        session = cli.get_client().getSession()

    try:
        us = session.getUpdateService()

        target = ProxyStringType()(targetstr)
        with open(studyfile) as f:
            rowkvs = get_pairs(f)
        links = create_map_annotation([target], rowkvs, ns)
        ids = us.saveAndReturnIds(links)
        print 'Created MapAnnotation links: %s' % ids
    finally:
        if cli:
            cli.close()


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('studyfile')
    parser.add_argument('target')
    args = parser.parse_args(args)
    run(args.studyfile, args.target)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
