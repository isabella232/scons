#! /usr/bin/env python
#
# SCons - a Software Constructor
#
# Copyright (c) 2001 Steven Knight
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

import getopt
import os
import os.path
import string
import sys
import traceback

# Strip the script directory from sys.path() so on case-insensitive
# (WIN32) systems Python doesn't think that the "scons" script is the
# "SCons" package.
sys.path = sys.path[1:]

import SCons.Node
import SCons.Node.FS
import SCons.Job
from SCons.Errors import *
import SCons.Sig
import SCons.Sig.MD5
from SCons.Taskmaster import Taskmaster

#
# Modules and classes that we don't use directly in this script, but
# which we want available for use in SConstruct and SConscript files.
#
from SCons.Environment import Environment
from SCons.Builder import Builder
from SCons.Defaults import *


#
# Task control.
#
class BuildTask(SCons.Taskmaster.Task):
    """An SCons build task."""
    def execute(self):
        if self.target.get_state() == SCons.Node.up_to_date:
            if self.top:
                print 'scons: "%s" is up to date.' % str(self.target)
        else:
            try:
                self.target.build()
            except BuildError, e:
                sys.stderr.write("scons: *** [%s] Error %d\n" % (e.node, e.stat))
                raise

    def failed(self):
        global ignore_errors
        if ignore_errors:
            SCons.Taskmaster.Task.executed(self)
        elif keep_going_on_error:
            SCons.Taskmaster.Task.fail_continue(self)
        else:
            SCons.Taskmaster.Task.fail_stop(self)

class CleanTask(SCons.Taskmaster.Task):
    """An SCons clean task."""
    def execute(self):
        if self.target.builder:
	    os.unlink(self.target.path)
	    print "Removed " + self.target.path


# Global variables

default_targets = []
include_dirs = []
help_option = None
num_jobs = 1
scripts = []
task_class = BuildTask	# default action is to build targets
current_func = None
calc = None
ignore_errors = 0
keep_going_on_error = 0

# utility functions

def _scons_syntax_error(e):
    """Handle syntax errors. Print out a message and show where the error
    occurred.
    """
    etype, value, tb = sys.exc_info()
    lines = traceback.format_exception_only(etype, value)
    for line in lines:
        sys.stderr.write(line+'\n')

def _scons_user_error(e):
    """Handle user errors. Print out a message and a description of the
    error, along with the line number and routine where it occured.
    """
    etype, value, tb = sys.exc_info()
    while tb.tb_next is not None:
        tb = tb.tb_next
    lineno = traceback.tb_lineno(tb)
    filename = tb.tb_frame.f_code.co_filename
    routine = tb.tb_frame.f_code.co_name
    sys.stderr.write("\nSCons error: %s\n" % value)
    sys.stderr.write('File "%s", line %d, in %s\n' % (filename, lineno, routine))

def _scons_user_warning(e):
    """Handle user warnings. Print out a message and a description of
    the warning, along with the line number and routine where it occured.
    """
    etype, value, tb = sys.exc_info()
    while tb.tb_next is not None:
        tb = tb.tb_next
    lineno = traceback.tb_lineno(tb)
    filename = tb.tb_frame.f_code.co_filename
    routine = tb.tb_frame.f_code.co_name
    sys.stderr.write("\nSCons warning: %s\n" % e)
    sys.stderr.write('File "%s", line %d, in %s\n' % (filename, lineno, routine))

def _scons_other_errors():
    """Handle all errors but user errors. Print out a message telling
    the user what to do in this case and print a normal trace.
    """
    print 'other errors'
    traceback.print_exc()



def Conscript(filename):
    global scripts
    scripts.append(filename)

def Default(*targets):
    for t in targets:
	for s in string.split(t):
	    default_targets.append(s)

def Help(text):
    global help_option
    if help_option == 'h':
	print text
	print "Use scons -H for help about command-line options."
	sys.exit(0)



#
# After options are initialized, the following variables are
# filled in:
#
option_list = []	# list of Option objects
short_opts = ""		# string of short (single-character) options
long_opts = []		# array of long (--) options
opt_func = {}		# mapping of option strings to functions

def options_init():
    """Initialize command-line options processing.
    
    This is in a subroutine mainly so we can easily single-step over
    it in the debugger.
    """

    class Option:
	"""Class for command-line option information.

	This exists to provide a central location for everything
	describing a command-line option, so that we can change
	options without having to update the code to handle the
	option in one place, the -h help message in another place,
	etc.  There are no methods here, only attributes.

	You can initialize an Option with the following:

	func	The function that will be called when this
		option is processed on the command line.
		Calling sequence is:

			func(opt, arg)

		If there is no func, then this Option probably
		stores an optstring to be printed.

	helpline
		The string to be printed in -h output.  If no
		helpline is specified but a help string is
		specified (the usual case), a helpline will be
		constructed automatically from the short, long,
		arg, and help attributes.  (In practice, then,
		setting helpline without setting func allows you
		to print arbitrary lines of text in the -h
		output.)

	short	The string for short, single-hyphen
		command-line options.
		Do not include the hyphen:

			'a' for -a, 'xy' for -x and -y, etc.

	long	An array of strings for long, double-hyphen
		command-line options.  Do not include
		the hyphens:

			['my-option', 'verbose']

	arg	If this option takes an argument, this string
		specifies how you want it to appear in the
		-h output ('DIRECTORY', 'FILE', etc.).

	help	The help string that will be printed for
		this option in the -h output.  Must be
		49 characters or fewer.

	future	If non-zero, this indicates that this feature
		will be supported in a future release, not
		the currently planned one.  SCons will
		recognize the option, but it won't show up
		in the -h output.

	The following attribute is derived from the supplied attributes:

	optstring
		A string, with hyphens, describing the flags
		for this option, as constructed from the
		specified short, long and arg attributes.

	All Option objects are stored in the global option_list list,
	in the order in which they're created.  This is the list
	that's used to generate -h output, so the order in which the
	objects are created is the order in which they're printed.

	The upshot is that specifying a command-line option and having
	everything work correctly is a matter of defining a function to
	process its command-line argument (set the right flag, update
	the right value), and then creating an appropriate Option object
	at the correct point in the code below.
	"""

	def __init__(self, func = None, helpline = None,
		 short = None, long = None, arg = None,
		 help = None, future = None):
	    self.func = func
	    self.short = short
	    self.long = long
	    self.arg = arg
	    self.help = help
	    opts = []
	    if self.short:
		for c in self.short:
		    if arg:
			c = c + " " + arg
		    opts = opts + ['-' + c]
	    if self.long:
		l = self.long
		if arg:
		    l = map(lambda x,a=arg: x + "=" + a, self.long)
		opts = opts + map(lambda x: '--' + x, l)
	    self.optstring = string.join(opts, ', ')
	    if helpline:
		self.helpline = helpline
	    elif help and not future:
		if len(self.optstring) <= 26:
		    sep = " " * (28 - len(self.optstring))
		else:
		    sep = self.helpstring = "\n" + " " * 30
		self.helpline = "  " + self.optstring + sep + self.help
	    else:
		self.helpline = None
	    global option_list
	    option_list.append(self)

    # Generic routine for to-be-written options, used by multiple
    # options below.

    def opt_not_yet(opt, arg):
        sys.stderr.write("Warning:  the %s option is not yet implemented\n"
			  % opt)

    # In the following instantiations, the help string should be no
    # longer than 49 characters.  Use the following as a guide:
    #	help = "1234567890123456789012345678901234567890123456789"

    def opt_ignore(opt, arg):
	sys.stderr.write("Warning:  ignoring %s option\n" % opt)

    Option(func = opt_ignore,
	short = 'bmSt', long = ['no-keep-going', 'stop', 'touch'],
	help = "Ignored for compatibility.")

    def opt_c(opt, arg):
        global task_class, calc
        task_class = CleanTask
        class CleanCalculator:
            def bsig(self, node):
                return None
            def csig(self, node):
                return None
            def current(self, node, sig):
                return 0
            def write(self):
                pass
        calc = CleanCalculator()

    Option(func = opt_c,
	short = 'c', long = ['clean', 'remove'],
	help = "Remove specified targets and dependencies.")

    Option(func = opt_not_yet, future = 1,
	long = ['cache-disable', 'no-cache'],
	help = "Do not retrieve built targets from Cache.")

    Option(func = opt_not_yet, future = 1,
	long = ['cache-force', 'cache-populate'],
	help = "Copy already-built targets into the Cache.")

    Option(func = opt_not_yet, future = 1,
	long = ['cache-show'],
	help = "Print what would have built Cached targets.")

    def opt_C(opt, arg):
	try:
	    os.chdir(arg)
	except:
	    sys.stderr.write("Could not change directory to 'arg'\n")

    Option(func = opt_C,
	short = 'C', long = ['directory'], arg = 'DIRECTORY',
	help = "Change to DIRECTORY before doing anything.")

    Option(func = opt_not_yet,
	short = 'd',
	help = "Print file dependency information.")

    Option(func = opt_not_yet, future = 1,
	long = ['debug'], arg = 'FLAGS',
	help = "Print various types of debugging information.")

    Option(func = opt_not_yet, future = 1,
	short = 'e', long = ['environment-overrides'],
	help = "Environment variables override makefiles.")

    def opt_f(opt, arg):
	global scripts
	scripts.append(arg)

    Option(func = opt_f,
	short = 'f', long = ['file', 'makefile', 'sconstruct'], arg = 'FILE',
	help = "Read FILE as the top-level SConstruct file.")

    def opt_help(opt, arg):
	global help_option
	help_option = 'h'

    Option(func = opt_help,
	short = 'h', long = ['help'],
	help = "Print defined help message, or this one.")

    def opt_help_options(opt, arg):
	global help_option
	help_option = 'H'

    Option(func = opt_help_options,
	short = 'H', long = ['help-options'],
	help = "Print this message and exit.")

    def opt_i(opt, arg):
        global ignore_errors
        ignore_errors = 1

    Option(func = opt_i,
	short = 'i', long = ['ignore-errors'],
	help = "Ignore errors from build actions.")

    def opt_I(opt, arg):
	global include_dirs
	include_dirs = include_dirs + [arg]

    Option(func = opt_I,
	short = 'I', long = ['include-dir'], arg = 'DIRECTORY',
	help = "Search DIRECTORY for imported Python modules.")

    def opt_j(opt, arg):
	global num_jobs
	try:
            num_jobs = int(arg)
	except:
            print UsageString()
            sys.exit(1)

	if num_jobs <= 0:
            print UsageString()
            sys.exit(1)

    Option(func = opt_j,
	short = 'j', long = ['jobs'], arg = 'N',
	help = "Allow N jobs at once.")

    def opt_k(opt, arg):
        global keep_going_on_error
        keep_going_on_error = 1

    Option(func = opt_k,
	short = 'k', long = ['keep-going'],
	help = "Keep going when a target can't be made.")

    Option(func = opt_not_yet, future = 1,
	short = 'l', long = ['load-average', 'max-load'], arg = 'N',
	help = "Don't start multiple jobs unless load is below N.")

    Option(func = opt_not_yet, future = 1,
	long = ['list-derived'],
	help = "Don't build; list files that would be built.")

    Option(func = opt_not_yet, future = 1,
	long = ['list-actions'],
	help = "Don't build; list files and build actions.")

    Option(func = opt_not_yet, future = 1,
	long = ['list-where'],
	help = "Don't build; list files and where defined.")

    def opt_n(opt, arg):
	SCons.Builder.execute_actions = None

    Option(func = opt_n,
	short = 'n', long = ['no-exec', 'just-print', 'dry-run', 'recon'],
	help = "Don't build; just print commands.")

    Option(func = opt_not_yet, future = 1,
	short = 'o', long = ['old-file', 'assume-old'], arg = 'FILE',
	help = "Consider FILE to be old; don't rebuild it.")

    Option(func = opt_not_yet, future = 1,
	long = ['override'], arg = 'FILE',
	help = "Override variables as specified in FILE.")

    Option(func = opt_not_yet, future = 1,
	short = 'p',
	help = "Print internal environments/objects.")

    Option(func = opt_not_yet, future = 1,
	short = 'q', long = ['question'],
	help = "Don't build; exit status says if up to date.")

    Option(func = opt_not_yet, future = 1,
	short = 'rR', long = ['no-builtin-rules', 'no-builtin-variables'],
	help = "Clear default environments and variables.")

    Option(func = opt_not_yet, future = 1,
	long = ['random'],
	help = "Build dependencies in random order.")

    def opt_s(opt, arg):
	SCons.Builder.print_actions = None

    Option(func = opt_s,
	short = 's', long = ['silent', 'quiet'],
	help = "Don't print commands.")

    Option(func = opt_not_yet, future = 1,
	short = 'u', long = ['up', 'search-up'],
	help = "Search up directory tree for SConstruct.")

    def option_v(opt, arg):
	print "SCons version __VERSION__, by Steven Knight et al."
	print "Copyright 2001 Steven Knight"
	sys.exit(0)

    Option(func = option_v,
	short = 'v', long = ['version'],
	help = "Print the SCons version number and exit.")

    Option(func = opt_not_yet, future = 1,
	short = 'w', long = ['print-directory'],
	help = "Print the current directory.")

    Option(func = opt_not_yet, future = 1,
	long = ['no-print-directory'],
	help = "Turn off -w, even if it was turned on implicitly.")

    Option(func = opt_not_yet, future = 1,
	long = ['write-filenames'], arg = 'FILE',
	help = "Write all filenames examined into FILE.")

    Option(func = opt_not_yet, future = 1,
	short = 'W', long = ['what-if', 'new-file', 'assume-new'], arg = 'FILE',
	help = "Consider FILE to be changed.")

    Option(func = opt_not_yet, future = 1,
	long = ['warn-undefined-variables'],
	help = "Warn when an undefined variable is referenced.")

    Option(func = opt_not_yet, future = 1,
	short = 'Y', long = ['repository'], arg = 'REPOSITORY',
	help = "Search REPOSITORY for source and target files.")

    global short_opts
    global long_opts
    global opt_func
    for o in option_list:
	if o.short:
	    if o.func:
		for c in o.short:
		    opt_func['-' + c] = o.func
	    short_opts = short_opts + o.short
	    if o.arg:
		short_opts = short_opts + ":"
	if o.long:
	    if o.func:
		for l in o.long:
		    opt_func['--' + l] = o.func
	    if o.arg:
		long_opts = long_opts + map(lambda a: a + "=", o.long)
	    else:
		long_opts = long_opts + o.long

options_init()



def UsageString():
    help_opts = filter(lambda x: x.helpline, option_list)
    s = "Usage: scons [OPTION] [TARGET] ...\n" + "Options:\n" + \
	string.join(map(lambda x: x.helpline, help_opts), "\n") + "\n"
    return s



def main():
    global scripts, help_option, num_jobs, task_class, calc

    targets = []

    # It looks like 2.0 changed the name of the exception class
    # raised by getopt.
    try:
	getopt_err = getopt.GetoptError
    except:
	getopt_err = getopt.error

    try:
	cmd_opts, t = getopt.getopt(string.split(os.environ['SCONSFLAGS']),
					  short_opts, long_opts)
    except KeyError:
	# It's all right if there's no SCONSFLAGS environment variable.
	pass
    except getopt_err, x:
	_scons_user_warning("SCONSFLAGS " + str(x))
    else:
	for opt, arg in cmd_opts:
	    opt_func[opt](opt, arg)

    try:
	cmd_opts, targets = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt_err, x:
	_scons_user_error(x)
    else:
	for opt, arg in cmd_opts:
	    opt_func[opt](opt, arg)

    if not scripts:
        for file in ['SConstruct', 'Sconstruct', 'sconstruct']:
            if os.path.isfile(file):
                scripts.append(file)
                break

    if help_option == 'H':
	print UsageString()
	sys.exit(0)

    if not scripts:
	if help_option == 'h':
	    # There's no SConstruct, but they specified either -h or
	    # -H.  Give them the options usage now, before we fail
	    # trying to read a non-existent SConstruct file.
	    print UsageString()
	    sys.exit(0)
	else:
	    raise UserError, "No SConstruct file found."

    # XXX The commented-out code here adds any "scons" subdirs in anything
    # along sys.path to sys.path.  This was an attempt at setting up things
    # so we can import "node.FS" instead of "SCons.Node.FS".  This doesn't
    # quite fit our testing methodology, though, so save it for now until
    # the right solutions pops up.
    #
    #dirlist = []
    #for dir in sys.path:
    #    scons = os.path.join(dir, 'scons')
    #    if os.path.isdir(scons):
    #     dirlist = dirlist + [scons]
    #    dirlist = dirlist + [dir]
    #
    #sys.path = dirlist

    sys.path = include_dirs + sys.path

    while scripts:
        file, scripts = scripts[0], scripts[1:]
	if file == "-":
	    exec sys.stdin in globals()
	else:
            try:
		f = open(file, "r")
	    except IOError, s:
		sys.stderr.write("Ignoring missing script '%s'\n" % file)
	    else:
		exec f in globals()

    if help_option == 'h':
	# They specified -h, but there was no Help() inside the
	# SConscript files.  Give them the options usage.
	print UsageString()
	sys.exit(0)

    if not targets:
	targets = default_targets

    nodes = map(lambda x: SCons.Node.FS.default_fs.Entry(x), targets)

    if not calc:
        calc = SCons.Sig.Calculator(SCons.Sig.MD5)

    taskmaster = SCons.Taskmaster.Taskmaster(nodes, task_class, calc)

    jobs = SCons.Job.Jobs(num_jobs, taskmaster)
    jobs.start()
    jobs.wait()

    SCons.Sig.write()

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        print "Build interrupted."
    except SyntaxError, e:
        _scons_syntax_error(e)
    except UserError, e:
        _scons_user_error(e)
    except:
        _scons_other_errors()
