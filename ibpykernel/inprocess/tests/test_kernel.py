# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import sys
import unittest

from ibpykernel.inprocess.blocking import BlockingInProcessKernelClient
from ibpykernel.inprocess.manager import InProcessKernelManager
from ibpykernel.inprocess.ipkernel import InProcessKernel
from ibpykernel.tests.utils import assemble_output
from IPython.testing.decorators import skipif_not_matplotlib
from IPython.utils.io import capture_output
from ipython_genutils import py3compat

if py3compat.PY3:
    from io import StringIO
else:
    from StringIO import StringIO


class InProcessKernelTestCase(unittest.TestCase):

    def setUp(self):
        self.km = InProcessKernelManager()
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        self.kc.wait_for_ready()

    @skipif_not_matplotlib
    def test_pylab(self):
        """Does %pylab work in the in-process kernel?"""
        kc = self.kc
        kc.execute('%pylab')
        out, err = assemble_output(kc.iopub_channel)
        self.assertIn('matplotlib', out)

    def test_raw_input(self):
        """ Does the in-process kernel handle raw_input correctly?
        """
        io = StringIO('foobar\n')
        sys_stdin = sys.stdin
        sys.stdin = io
        try:
            if py3compat.PY3:
                self.kc.execute('x = input()')
            else:
                self.kc.execute('x = raw_input()')
        finally:
            sys.stdin = sys_stdin
        self.assertEqual(self.km.kernel.shell.user_ns.get('x'), 'foobar')

    def test_stdout(self):
        """ Does the in-process kernel correctly capture IO?
        """
        kernel = InProcessKernel()

        with capture_output() as io:
            kernel.shell.run_cell('print("foo")')
        self.assertEqual(io.stdout, 'foo\n')

        kc = BlockingInProcessKernelClient(kernel=kernel, session=kernel.session)
        kernel.frontends.append(kc)
        kc.execute('print("bar")')
        out, err = assemble_output(kc.iopub_channel)
        self.assertEqual(out, 'bar\n')

    def test_getpass_stream(self):
        "Tests that kernel getpass accept the stream parameter"
        kernel = InProcessKernel()
        kernel._allow_stdin = True
        kernel._input_request = lambda *args, **kwargs : None

        kernel.getpass(stream='non empty')
