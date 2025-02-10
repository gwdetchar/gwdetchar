# coding=utf-8
# Copyright (C) Evan Goetz (2025)
#
# This file is part of the GW DetChar python package.
#
# GW DetChar is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GW DetChar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GW DetChar.  If not, see <http://www.gnu.org/licenses/>.

"""Custom summary page to display events queried from the Gravitational-wave
Candidate Event Database (GraceDb)
"""

from collections import OrderedDict
from MarkupPy import markup
import os
import re

from ligo.gracedb.rest import GraceDb as GrDB
from ligo.gracedb.exceptions import HTTPError
from gwpy.time import from_gps, to_gps

__author__ = 'Evan Goetz <evan.goetz@ligo.org>'
__credits__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

LABELS = OrderedDict()
LABELS["danger"] = {
    "ADVNO",
    "DQV",
    "H1NO",
    "L1NO",
    "V1NO",
}
LABELS["warning"] = {
    "INJ",
}
LABELS["success"] = {
    'GCN_PRELIM_SENT',
}
re_quote = re.compile(r'^[\s\"\']+|[\s\"\']+$')
re_cchar = re.compile(r"[\W_]+")


class GraceDb(object):
    """GraceDB object type.
    """
    type = 'gracedb'

    def __init__(self, name, start, end, url='https://gracedb.ligo.org',
                 query='External', columns=['gpstime', 'date', 'pipeline'],
                 headers=['GPS time', 'UTC time', 'Source'], rank='gpstime',
                 **kwargs):
        self.name = name
        self.start = to_gps(start)
        self.end = to_gps(end)
        self.url = url
        self.query = f'{query} {int(self.start)} .. {int(self.end)}'
        self.events = dict()
        self.headers = headers
        self.columns = columns
        self.rank = rank
        self.states = []

    def process(self):
        # query gracedb
        service_url = f'{self.url}/api/'
        self.connection = GrDB(service_url=service_url)
        self.exception = HTTPError
        print(f'Connected to gracedb at {service_url}')
        try:
            self.events[None] = list(self.connection.superevents(self.query))
            self._query_type = 'S'
        except self.exception:
            self.events[None] = list(self.connection.events(self.query))
            event_method = self.connection.event
            eventid_name = 'graceid'
            self._query_type = 'E'
        else:
            event_method = self.connection.superevent
            eventid_name = 'superevent_id'
            for event in self.events[None]:  # get preferred event parameters
                event.update(self.connection.event(
                    event['preferred_event'],
                ).json())
        print(f'Recovered {len(self.events[None])} events for query '
              f'{self.query}\n')
        if 'labels' in self.columns:
            for e in self.events[None]:
                e['labels'] = ', '.join(event_method(
                    e[eventid_name]).json()['labels'])
            print('Downloaded labels')

    def process_state(self, state):
        def in_state(event):
            return int(event['gpstime']) in state.active
        self.events[str(state)] = list(filter(in_state, self.events[None]))
        reverse = self.rank not in ['gpstime', 'far']
        self.events[str(state)].sort(key=lambda x: x[self.rank],
                                     reverse=reverse)
        self.states.append(state.name)
        print(f'    Selected {len(self.events[str(state)])} events')

    def write_state_html(self, state, output_path):
        """Write the '#main' HTML content for this `GraceDbTab`.
        """
        page = markup.page()
        # build table of events
        page.table(class_='table table-sm table-hover table-striped mt-2',
                   id_='gracedb')
        # thead
        page.thead()
        page.tr()
        for head in self.headers:
            page.th(head)
        page.tr.close()
        page.thead.close()
        # tbody
        page.tbody()
        for event in sorted(self.events[str(state)],
                            key=lambda e: e['gpstime']):
            context = None
            try:
                labs = set(event['labels'].split(', '))
            except (AttributeError, KeyError):
                pass
            else:
                for ctx, labels in LABELS.items():
                    if (
                            ctx == 'success' and labs.union(labels) == labs or
                            labs.intersection(labels)
                    ):
                        context = ctx
                        break
            if context:
                page.tr(class_='table-%s' % context)
            else:
                page.tr()
            for col in self.columns:
                if col == 'date':
                    gpskey = 't_0' if 'superevent_id' in event else 'gpstime'
                    page.td(from_gps(event[gpskey]).strftime(
                        '%B %d %Y %H:%M:%S.%f',
                    )[:-3])
                    continue
                elif col.lower() == 'dqr' and 'superevent_id' in event:
                    page.td()
                    sid = event['superevent_id']
                    href = (f'{self.url}/apiweb/superevents/{sid}/files/'
                            'dqr.html')
                    try:
                        self.connection.get(href)
                    except self.exception:
                        page.p('&mdash;')
                    else:
                        title = f'Data-quality report for {sid}'
                        page.a('DQR', title=title, href=href, target='_blank',
                               rel='external', class_='btn btn-info btn-sm')
                    page.td.close()
                    continue
                elif col.lower() == 'dqr':
                    page.td()
                    page.p('&mdash;')
                    page.td.close()
                    continue
                try:
                    v = event[col]
                except KeyError:
                    try:
                        v = event['extra_attributes']['GRB'][col]
                        assert v is not None
                    except (KeyError, AssertionError):
                        page.td('-')
                        continue
                if col in ('graceid', 'superevent_id', 'preferred_event'):
                    page.td()
                    tag = 'superevents' if col == 'superevent_id' else 'events'
                    href = f'{self.url}/{tag}/view/{v}'
                    title = f'GraceDB {tag[:-1]} page for {v}'
                    page.a(v, title=title, href=href, target='_blank',
                           rel='external', class_='btn btn-info btn-sm')
                    page.td.close()
                elif col not in ('gpstime', 't_0') and isinstance(v, float):
                    page.td(f'{v:.3g}')
                elif col == 'labels':
                    page.td(', '.join(
                        [f'<samp>{iterable}</samp>'
                         for iterable in sorted(labs)]))
                else:
                    page.td(str(v))
            page.tr.close()
        page.tbody.close()
        page.table.close()
        if len(self.events[str(state)]) == 0:
            page.p('No events were recovered for this state.')
        else:
            page.button(
                'Export to CSV',
                class_='btn btn-outline-secondary btn-table mt-2',
                **{'data-table-id': 'gracedb', 'data-filename': 'gracedb.csv'})

        # query doc
        qurl = (f'{self.url}/search/?query='
                f"{self.query.replace(' ', '+')}&query_type="
                f"{getattr(self, '_query_type', 'E')}&results_format=S")
        qlink = markup.oneliner.a(
            'here',
            href=qurl,
            target='_blank',
        )
        page.p(f'The above table was generated from a query to {self.url} '
               f'with the form <code>{self.query}</code>. To view the results '
               'of the same query via the GraceDB web interface, click '
               f'{qlink}.',
               class_='mt-2')

        # reference the labelling
        page.h4('Labelling reference')
        page.p('Events in the above table may have a context based on '
               'its labels as follows:')
        for c, labels in LABELS.items():
            c = (c if c == 'warning' else f'{c} text-white')
            labstr = ', '.join([f'<samp>{item}</samp>'
                                for item in sorted(labels)])
            page.p(labstr, class_='bg-%s pl-2' % c, style='width: auto;')

        # write to file
        with open(os.path.join(output_path, state.description), 'w') as fobj:
            fobj.write(str(page))
