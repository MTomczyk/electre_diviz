#!/usr/bin/env python

"""
ElectreDiscordance - computes partial (i.e. per-criterion) discordance matrix
using procedure which is common to the most methods from the Electre family.

The key feature of this module is its flexibility in terms of the types of
elements allowed to compare, i.e. alternatives vs alternatives, alternatives vs
boundary profiles and alternatives vs central (characteristic) profiles.

Usage:
    ElectreDiscordance.py -i DIR -o DIR

Options:
    -i DIR     Specify input directory. It should contain the following files:
                   alternatives.xml
                   classes_profiles.xml (optional)
                   criteria.xml
                   method_parameters.xml
                   performance_table.xml
                   profiles_performance_table.xml (optional)
    -o DIR     Specify output directory. Files generated as output:
                   discordance.xml
                   messages.xml
    --version  Show version.
    -h --help  Show this screen.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import traceback

from docopt import docopt

from common import comparisons_to_xmcda, create_messages_file, get_dirs, \
    get_error_message, get_input_data, write_xmcda, Vividict

__version__ = '0.2.0'


def get_discordance(comparables_a, comparables_perf_a, comparables_b,
                    comparables_perf_b, criteria, thresholds, pref_directions):

    # XXX exactly the same as in ElectreConcordance
    # 'x' and 'y' to keep it as general as possible
    def _omega(x, y):
        if pref_directions[criterion] == 'max':
            return x - y
        if pref_directions[criterion] == 'min':
            return y - x

    def _get_partial_discordance(x, y, criterion):
        p = thresholds[criterion].get('preference', 0)
        v = thresholds[criterion].get('veto')
        if not v:
            return 0.0
        if _omega(x, y) >= -p:
            return 0.0
        elif _omega(x, y) < -v:
            return 1.0
        else:
            return (_omega(x, y) + p) / (p - v)

    two_way_comparison = True if comparables_a != comparables_b else False
    partial_discordance = Vividict()
    for a in comparables_a:
        for b in comparables_b:
            for criterion in criteria:
                pc = _get_partial_discordance(comparables_perf_a[a][criterion],
                                              comparables_perf_b[b][criterion],
                                              criterion)
                partial_discordance[a][b][criterion] = pc
                if two_way_comparison:
                    pc = _get_partial_discordance(comparables_perf_b[b][criterion],
                                                  comparables_perf_a[a][criterion],
                                                  criterion)
                    partial_discordance[b][a][criterion] = pc
    return partial_discordance


def main():
    try:
        args = docopt(__doc__, version=__version__)
        output_dir = None
        input_dir, output_dir = get_dirs(args)
        filenames = [
            # every tuple below == (filename, is_optional)
            ('alternatives.xml', False),
            ('classes_profiles.xml', True),
            ('criteria.xml', False),
            ('method_parameters.xml', False),
            ('performance_table.xml', False),
            ('profiles_performance_table.xml', True),
        ]
        params = [
            'alternatives',
            'categories_profiles',
            'comparison_with',
            'criteria',
            'performances',
            'pref_directions',
            'profiles_performance_table',
            'thresholds',
        ]
        d = get_input_data(input_dir, filenames, params)

        # getting the elements to compare
        comparables_a = d.alternatives
        comparables_perf_a = d.performances
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            # central_profiles is a dict, so we need to get the keys
            comparables_b = [i for i in d.categories_profiles]
            comparables_perf_b = d.profiles_performance_table
        else:
            comparables_b = d.alternatives
            comparables_perf_b = d.performances

        discordance = get_discordance(comparables_a, comparables_perf_a,
                                      comparables_b, comparables_perf_b,
                                      d.criteria, d.thresholds,
                                      d.pref_directions)

        # serialization etc.
        if d.comparison_with in ('boundary_profiles', 'central_profiles'):
            mcda_concept = 'alternativesProfilesComparisons'
        else:
            mcda_concept = None
        comparables = (comparables_a, comparables_b)
        xmcda = comparisons_to_xmcda(discordance, comparables,
                                     use_partials=True,
                                     mcda_concept=mcda_concept)
        write_xmcda(xmcda, os.path.join(output_dir, 'discordance.xml'))
        create_messages_file(None, ('Everything OK.',), output_dir)
        return 0
    except Exception, err:
        err_msg = get_error_message(err)
        log_msg = traceback.format_exc()
        print(log_msg.strip())
        create_messages_file((err_msg, ), (log_msg, ), output_dir)
        return 1


if __name__ == '__main__':
    sys.exit(main())
