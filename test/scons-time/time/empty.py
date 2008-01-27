#!/usr/bin/env python
#
# __COPYRIGHT__
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"

"""
Verify that the time subcommand doesn't fail and prints an appropriate
error message if a log file is empty.
"""

import TestSCons_time

test = TestSCons_time.TestSCons_time()


header = '       Total  SConscripts        SCons     commands\n'

lines = []

line_fmt    = '   11.123456    22.234567    33.345678    44.456789    %s\n'
empty_fmt   = '                                                       %s\n'

for i in xrange(9):
    logfile_name = 'foo-%s.log' % i
    if i == 5:
        test.write(test.workpath(logfile_name), "")
        lines.append(empty_fmt % logfile_name)
    else:
        test.fake_logfile(logfile_name)
        lines.append(line_fmt % logfile_name)

expect = [header] + lines

test.run(arguments = 'time foo-*.log',
         stdout = ''.join(expect),
         stderr = "file 'foo-5.log' has no contents!\n")

test.pass_test()