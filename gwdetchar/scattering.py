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

"""Utilities for analysing optical scattering
"""

import numpy

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'

OPTIC_MOTION_CHANNELS = {
    'BS': ['SUS-BS_M1_DAMP_L_IN1_DQ'],
    'ETMX': ['SUS-ETMX_M0_DAMP_L_IN1_DQ',
             'SUS-ETMX_R0_DAMP_L_IN1_DQ'],
    'ETMY': ['SUS-ETMY_M0_DAMP_L_IN1_DQ',
             'SUS-ETMY_R0_DAMP_L_IN1_DQ'],
    'IM1': ['SUS-IM1_M1_DAMP_L_IN1_DQ'],
    'IM2': ['SUS-IM2_M1_DAMP_L_IN1_DQ'],
    'IM3': ['SUS-IM3_M1_DAMP_L_IN1_DQ'],
    'IM4': ['SUS-IM4_M1_DAMP_L_IN1_DQ'],
    'ITMX': ['SUS-ITMX_M0_DAMP_L_IN1_DQ',
             'SUS-ITMX_R0_DAMP_L_IN1_DQ'],
    'ITMY': ['SUS-ITMY_M0_DAMP_L_IN1_DQ',
             'SUS-ITMY_R0_DAMP_L_IN1_DQ'],
    'MC1': ['SUS-MC1_M1_DAMP_L_IN1_DQ'],
    'MC2': ['SUS-MC2_M1_DAMP_L_IN1_DQ'],
    'MC3': ['SUS-MC3_M1_DAMP_L_IN1_DQ'],
    'OM1': ['SUS-OM1_M1_DAMP_L_IN1_DQ'],
    'OM2': ['SUS-OM2_M1_DAMP_L_IN1_DQ'],
    'OM3': ['SUS-OM3_M1_DAMP_L_IN1_DQ'],
    'OMC': ['SUS-OMC_M1_DAMP_L_IN1_DQ'],
    'PR2': ['SUS-PR2_M1_DAMP_L_IN1_DQ'],
    'PR3': ['SUS-PR3_M1_DAMP_L_IN1_DQ'],
    'PRM': ['SUS-PRM_M1_DAMP_L_IN1_DQ'],
    'RM1': ['SUS-RM1_M1_DAMP_L_IN1_DQ'],
    'RM2': ['SUS-RM2_M1_DAMP_L_IN1_DQ'],
    'ZM1': ['SUS-ZM1_M1_DAMP_L_IN1_DQ'],
    'ZM2': ['SUS-ZM2_M1_DAMP_L_IN1_DQ'],
    'OPO': ['SUS-OPO_M1_DAMP_L_IN1_DQ'],
    'OFI': ['SUS-OFI_M1_DAMP_L_IN1_DQ',
            'SUS-OFI_M1_DAMP_T_IN1_DQ'],
    'SR2': ['SUS-SR2_M1_DAMP_L_IN1_DQ'],
    'SR3': ['SUS-SR3_M1_DAMP_L_IN1_DQ'],
    'SRM': ['SUS-SRM_M1_DAMP_L_IN1_DQ'],
    'TMSX': ['SUS-TMSX_M1_DAMP_L_IN1_DQ'],
    'TMSY': ['SUS-TMSY_M1_DAMP_L_IN1_DQ'],
}

FREQUENCY_MULTIPLIERS = range(1, 5)


def get_fringe_frequency(timeseries, multiplier=2.0):
    """Calculate the scattering fringe frequency from a optic motion timeseries
    """
    velocity = timeseries.diff()
    velocity.override_unit('m/s')  # just so multiplication works
    fringef = numpy.abs(multiplier * 2. / 1.064 * velocity *
                        velocity.sample_rate.value)
    fringef.override_unit('Hz')
    return fringef
