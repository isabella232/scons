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
Verify that the Chmod() Action works.
"""

import os
import os.path
import stat

import TestSCons

test = TestSCons.TestSCons()

# Note:  Win32 basically has two modes that it can os.chmod() files to
# 0444 and 0666, and directories to 0555 and 0777, so we can only really
# oscillate between those values.
test.write('SConstruct', """
Execute(Chmod('f1', 0666))
Execute(Chmod('d2', 0777))
def cat(env, source, target):
    target = str(target[0])
    source = map(str, source)
    f = open(target, "wb")
    for src in source:
        f.write(open(src, "rb").read())
    f.close()
Cat = Action(cat)
env = Environment()
env.Command('bar.out', 'bar.in', [Cat,
                                  Chmod("f3", 0666),
                                  Chmod("d4", 0777)])
env = Environment(FILE = 'f5')
env.Command('f6.out', 'f6.in', [Chmod('$FILE', 0666), Cat])
env.Command('f7.out', 'f7.in', [Cat,
                                Chmod('Chmod-$SOURCE', 0666),
                                Chmod('${TARGET}-Chmod', 0666)])
""")

test.write('f1', "f1\n")
test.subdir('d2')
test.write(['d2', 'file'], "d2/file\n")
test.write('bar.in', "bar.in\n")
test.write('f3', "f3\n")
test.subdir('d4')
test.write(['d4', 'file'], "d4/file\n")
test.write('f5', "f5\n")
test.write('f6.in', "f6.in\n")
test.write('f7.in', "f7.in\n")
test.write('Chmod-f7.in', "Chmod-f7.in\n")
test.write('f7.out-Chmod', "f7.out-Chmod\n")

os.chmod(test.workpath('f1'), 0444)
os.chmod(test.workpath('d2'), 0555)
os.chmod(test.workpath('f3'), 0444)
os.chmod(test.workpath('d4'), 0555)
os.chmod(test.workpath('f5'), 0444)
os.chmod(test.workpath('Chmod-f7.in'), 0444)
os.chmod(test.workpath('f7.out-Chmod'), 0444)

expect = test.wrap_stdout(read_str = 'Chmod("f1", 0666)\nChmod("d2", 0777)\n',
                          build_str = """\
cat(["bar.out"], ["bar.in"])
Chmod("f3", 0666)
Chmod("d4", 0777)
Chmod("f5", 0666)
cat(["f6.out"], ["f6.in"])
cat(["f7.out"], ["f7.in"])
Chmod("Chmod-f7.in", 0666)
Chmod("f7.out-Chmod", 0666)
""")
test.run(options = '-n', arguments = '.', stdout = expect)

s = stat.S_IMODE(os.stat(test.workpath('f1'))[stat.ST_MODE])
test.fail_test(s != 0444)
s = stat.S_IMODE(os.stat(test.workpath('d2'))[stat.ST_MODE])
test.fail_test(s != 0555)
test.must_not_exist('bar.out')
s = stat.S_IMODE(os.stat(test.workpath('f3'))[stat.ST_MODE])
test.fail_test(s != 0444)
s = stat.S_IMODE(os.stat(test.workpath('d4'))[stat.ST_MODE])
test.fail_test(s != 0555)
s = stat.S_IMODE(os.stat(test.workpath('f5'))[stat.ST_MODE])
test.fail_test(s != 0444)
test.must_not_exist('f6.out')
test.must_not_exist('f7.out')
s = stat.S_IMODE(os.stat(test.workpath('Chmod-f7.in'))[stat.ST_MODE])
test.fail_test(s != 0444)
s = stat.S_IMODE(os.stat(test.workpath('f7.out-Chmod'))[stat.ST_MODE])
test.fail_test(s != 0444)

test.run()

s = stat.S_IMODE(os.stat(test.workpath('f1'))[stat.ST_MODE])
test.fail_test(s != 0666)
s = stat.S_IMODE(os.stat(test.workpath('d2'))[stat.ST_MODE])
test.fail_test(s != 0777)
test.must_match('bar.out', "bar.in\n")
s = stat.S_IMODE(os.stat(test.workpath('f3'))[stat.ST_MODE])
test.fail_test(s != 0666)
s = stat.S_IMODE(os.stat(test.workpath('d4'))[stat.ST_MODE])
test.fail_test(s != 0777)
s = stat.S_IMODE(os.stat(test.workpath('f5'))[stat.ST_MODE])
test.fail_test(s != 0666)
test.must_match('f6.out', "f6.in\n")
test.must_match('f7.out', "f7.in\n")
s = stat.S_IMODE(os.stat(test.workpath('Chmod-f7.in'))[stat.ST_MODE])
test.fail_test(s != 0666)
s = stat.S_IMODE(os.stat(test.workpath('f7.out-Chmod'))[stat.ST_MODE])
test.fail_test(s != 0666)

test.pass_test()
