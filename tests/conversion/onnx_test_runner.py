# Copyright (c) 2017 The Khronos Group Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division, print_function, absolute_import

import os
import unittest

from nnef_tools import convert
from nnef_tools.io.onnx import onnx_io


class ONNXTestRunner(unittest.TestCase):
    def _test_model(self, filename, run=True, compare=True, source_shape="None", custom_converters=None):
        if custom_converters is None:
            custom_converters = []

        convs = ["custom.onnx_to_nnef_" + conv for conv in custom_converters]
        network_name = filename.rsplit('/', 1)[1].rsplit('.', 1)[0].replace('.', '_').replace('-', '_')
        print(filename)
        command = """
        ./nnef_tools/convert.py --input-format=onnx \\
                                --output-format=nnef \\
                                --input-model={} \\
                                --output-model=out/nnef/{}.nnef \\
                                --input-shape="{}" \\
                                --custom-converters="{}" \\
                                --permissive \\
                                --conversion-info
        """.format(filename, network_name, source_shape, ','.join(convs))
        print(command)
        convert.convert_using_command(command)

        convs = ["custom.nnef_to_onnx_" + conv for conv in custom_converters]
        command = """
        ./nnef_tools/convert.py --input-format=nnef \\
                                --output-format=onnx \\
                                --input-model=out/nnef/{}.nnef \\
                                --output-model=out/onnx/{}.onnx \\
                                --custom-converters="{}" \\
                                --permissive \\
                                --conversion-info
        """.format(network_name, network_name, ','.join(convs))
        print(command)
        convert.convert_using_command(command)

        filename2 = os.path.join('out', 'onnx', network_name + '.onnx')

        g = onnx_io.read_onnx_from_protobuf(filename2)
        input_shapes = [input.shape for input in g.inputs]
        input_dtypes = [input.dtype for input in g.inputs]

        del g

        activation_testing = int(os.environ.get('NNEF_ACTIVATION_TESTING', '1'))
        print("Activation testing is", "ON" if activation_testing else "OFF")
        if activation_testing:
            import numpy as np
            import caffe2.python.onnx.backend as backend
            import onnx

            def check_onnx_model(filename):
                model = onnx.load(filename)
                onnx.checker.check_model(model)

            def run_onnx_model(filename, input):
                model = onnx.load(filename)
                try:
                    rep = backend.prepare(model, device="CUDA:0")
                    outputs = rep.run(input)
                except Exception:
                    print("Couldn't run in CUDA, running on CPU:")
                    rep = backend.prepare(model, device="CPU")
                    outputs = rep.run(input)

                return outputs

            check_onnx_model(filename2)

            if run:
                inputs = []
                for input_shape, input_dtype in zip(input_shapes, input_dtypes):
                    if input_dtype == 'FLOAT':
                        inputs.append(np.random.random(input_shape).astype(np.float32) * 0.8 + 0.1)
                    elif input_dtype == 'BOOL':
                        inputs.append(np.random.random(input_shape) > 0.5)
                    elif input_dtype == 'INT64':
                        inputs.append((np.random.random(input_shape) * 1000).astype(np.int32))
                    else:
                        assert False

                outputs = None
                if compare:
                    print('Running original ONNX:')
                    outputs = run_onnx_model(filename, inputs)

                print('Running our ONNX:')
                outputs2 = run_onnx_model(filename2, inputs)

                if compare:
                    print('Comparing:')
                    for output, output2 in zip(outputs, outputs2):
                        # print('Max dist:', np.max(np.abs(output-output2)))
                        self.assertTrue(np.all(np.isfinite(output)))
                        self.assertTrue(np.all(np.isfinite(output2)))
                        self.assertTrue(np.allclose(output, output2, atol=1e-5))