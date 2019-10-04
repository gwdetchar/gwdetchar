# coding=utf-8
# Copyright (C) Duncan Macleod (2015)
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

"""Utilities for accessing information from CDS
"""

from urllib import request

RTDCUID_URL = (
    'https://daqsvn.ligo-la.caltech.edu/websvn/filedetails.php?'
    'repname=daq_maps&path=%2F{ifo}%2Frtdcuid'
)

ADCLIST_URL = (
    'https://daqsvn.ligo-la.caltech.edu/websvn/filedetails.php?'
    'repname=daq_maps&path=%2F{ifo}%2Fadclists%2F{model}_adclist.txt'
)

DCUID_MAP = {}
ADC_MAP = {}

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


def get_dcuid_map(ifo):
    import bs4
    html = request.urlopen(RTDCUID_URL.format(ifo=ifo.lower())).read()
    soup = bs4.BeautifulSoup(html, 'lxml')
    listing = soup.find('div', attrs={'class': 'listing'})
    mapping = {}
    for code in listing.find_all('code'):
        try:
            fec, model = str(code.get_text()).rstrip(' \n').split()
            fec = int(fec)
        except (ValueError, TypeError):
            continue
        else:
            mapping[fec] = model
    return mapping


def get_adclist(ifo, model):
    import bs4
    html = request.urlopen(ADCLIST_URL.format(ifo=ifo.lower(),
                                              model=model.lower())).read()
    soup = bs4.BeautifulSoup(html, 'lxml')
    listing = soup.find('div', attrs={'class': 'listing'})
    mapping = {}
    for code in listing.find_all('code'):
        try:
            card, slot, channel, part = str(
                code.get_text()).rstrip(' \n').split()
            card = int(card)
            slot = int(slot)
        except (ValueError, TypeError):
            continue
        else:
            mapping[(card, slot)] = channel
    return mapping


def model_name_from_dcuid(ifo, dcuid):
    global DCUID_MAP
    if ifo not in DCUID_MAP:
        DCUID_MAP[ifo] = get_dcuid_map(ifo)
    try:
        return DCUID_MAP[ifo][dcuid]
    except KeyError as e:
        e.args = ('No model name associated with DCUID=%d' % dcuid,)
        raise


def dcuid_from_model_name(ifo, model):
    global DCUID_MAP
    if ifo not in DCUID_MAP:
        DCUID_MAP[ifo] = get_dcuid_map(ifo)
    for dcuid, name in DCUID_MAP[ifo].items():
        if model.lower() == name:
            return dcuid
    raise KeyError("No DCUID associated with model=%r" % model)


def get_adc_channel(ifo, model, card, slot):
    global ADC_MAP
    ADC_MAP.setdefault(ifo, {})
    if model not in ADC_MAP[ifo]:
        ADC_MAP[ifo][model] = get_adclist(ifo, model)
    try:
        return ADC_MAP[ifo][model][(card, slot)]
    except KeyError as e:
        e.args = ('No channel associated with card %d, slot %d for %s'
                  % (card, slot, model),)
        raise


def get_real_channel(adcchannel):
    main = str(adcchannel).split('-', 1)[1]
    ifo = str(adcchannel).split(':')[0]
    dcuid, type_, _, _, card, slot = main.split('_')
    if type_ != 'ADC':
        raise ValueError("No 'real' channel map for non-ADC channels")
    modelname = model_name_from_dcuid(ifo, int(dcuid))
    return get_adc_channel(ifo, modelname, int(card), int(slot))
