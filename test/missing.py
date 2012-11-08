#!/usr/bin/env python
##
#
# Copyright 2012 Andy Georges
#
# This file is part of VSC-tools,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://vscentrum.be/nl/en),
# the Hercules foundation (http://www.herculesstichting.be/in_English)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# http://github.com/hpcugent/VSC-tools
#
# VSC-tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# VSC-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with VSC-tools. If not, see <http://www.gnu.org/licenses/>.
##
"""
Tests for the vsc.utils.missing module.
"""
from paycheck import with_checker
from unitest import TestCase, TestLoader

from vsc.utils.missing import nub


class TestNub(TestCase):
    """Test for the nub function."""

    @with_checker([int])
    def test_length(self, list_of_ints):
        nubbed = nub(list_of_ints)
        self.assertTrue(len(list_of_ints) >= len(nubbed))

    @with_checker([int])
    def test_membership(self, list_of_ints):
        nubbed = nub(list_of_ints)
        for x in list_of_ints:
            self.assertTrue(x in nubbed)

    @with_checker([int])
    def test_order(self, list_of_ints):
        nubbed = nub(2 * list_of_ints)
        for (x, y) in [(x_, y_) for x_ in list_of_ints for y_ in list_of_ints]:
            self.assertTrue((list_of_ints.index(x) <= list_of_ints.index(y)) == (nubbed.index(x) <= nubbed.index(y)))

def suite():
    """ return all the tests"""
    return TestLoader().loadTestsFromTestCase(TestNub)
