'''Test the pipeline module.'''
from __future__ import absolute_import, print_function, division

from simtools.pipelines import PipelineStage, Pipeline, PipelineData


class Increment(PipelineStage):
    '''A simple pipeline stage that prints a number and increments by one.'''
    def __call__(self, data_in):
        print(data_in.items['num'])
        data_in.items['num'] += 1
        return data_in


def function_stage(data_in):
    print(data_in.items['num'])
    data_in.items['num'] += 1
    return data_in


class TestPipeline(object):
    '''Test the pipeline class.'''

    def _test(self, num):
        '''Insert ``num`` simple stages into the pipeline and run it.'''
        pipeline = Pipeline()
        assert pipeline.num_stages == 0

        for n_stage in range(num):
            increment_stage = Increment()
            pipeline.append(increment_stage)
            assert pipeline.num_stages == n_stage + 1

        data = PipelineData()
        data.items['num'] = 0
        data = pipeline.run(data)

        assert data.items['num'] == num

    def test_increment(self):
        '''Test a simple increment procedure.'''
        # Empty pipeline should run but do nothing.
        self._test(0)
        # One, two, ten
        self._test(1)
        self._test(2)
        self._test(10)

    def test_stage_as_function(self):
        '''Test the pipeline when only a simple function is added into the list
        of stages.'''
        pipeline = Pipeline()
        pipeline.append(function_stage)
        pipeline.append(Increment())

        data = PipelineData()
        data.items['num'] = 0
        data = pipeline.run(data)

        assert data.items['num'] == 2
