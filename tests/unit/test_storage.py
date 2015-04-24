'''Tests of the simtools.storage package.'''

import numpy as np
import collections
import numbers

import pytest
from simtools.storage import DataStorage

notImplMsg = "Not implemented"

class TestHDF5Storage(object):
    def getItem(self, d, key):
        return d[key]

    def test_basic_types(self):
        ds = DataStorage.open('test_basic_types.h5', 'w')

        test_int      = 124
        test_float    = 0.1
        test_1d_array = np.arange(1000000)
        test_2d_array = np.random.rand(100, 100)
        test_list     = [1, 2, 3, 4]
        test_dict     = dict(int=123,
                             float=111.1,
                             list=test_list)

        ds['int']      = test_int
        ds['float']    = test_float
        ds['1d_array'] = test_1d_array
        ds['2d_array'] = test_2d_array
        ds['list']     = test_list
        ds['dict']     = test_dict

        # Test return types
        assert isinstance(ds['int'], numbers.Integral)
        assert isinstance(ds['float'], float)
        assert isinstance(ds['1d_array'], np.ndarray)
        assert isinstance(ds['2d_array'], np.ndarray)
        assert isinstance(ds['list'], collections.MutableSequence)
        assert isinstance(ds['dict'], collections.MutableMapping)

        # Test values of basic types
        assert ds['int'] == test_int
        assert ds['float'] == test_float
        assert np.all(ds['1d_array'] == test_1d_array)
        assert np.all(ds['2d_array'] == test_2d_array)
        assert ds['list'] == test_list
        assert ds['dict'] == test_dict

        ds.flush()

        # Test delete
        del ds['int']
        with pytest.raises(KeyError):
            self.getItem(ds, 'int')

        del ds['float']
        with pytest.raises(KeyError):
            self.getItem(ds, 'float')

        del ds['1d_array']
        with pytest.raises(KeyError):
            self.getItem(ds, '1d_array')

        del ds['2d_array']
        with pytest.raises(KeyError):
            self.getItem(ds, '2d_array')

        del ds['list']
        with pytest.raises(KeyError):
            self.getItem(ds, 'list')

        del ds['dict']
        with pytest.raises(KeyError):
            self.getItem(ds, 'dict')

        ds.close()

        # ds should be empty now
        ds = DataStorage.open('test_basic_types.h5', 'r')
        assert len(ds) == 0

        ds.close()

    def test_lists(self):
        def appendListAndTest(ds, key, test_l, item):
            ds[key].append(item)
            test_l.append(item)
            assert test_l == ds[key]

        ds = DataStorage.open('test_lists.h5', 'w')

        d1 = {"hola" : [10, 20, 30],
              "str" : "This is a test string"}

        test_list = [1, 2, d1]
        ds['list'] = test_list
        ds.close()

        ds = DataStorage.open('test_lists.h5', 'r+')
        appendListAndTest(ds, 'list', test_list, 10)
        appendListAndTest(ds, 'list', test_list, 23.5)
        appendListAndTest(ds, 'list', test_list, [1, 2, 3])
        appendListAndTest(ds, 'list', test_list, dict(a=10, b=[1, 2, 3]))
        ds.close()

    def test_iterator(self):
        ds = DataStorage.open('test_iterator.h5', 'w')

        test_list = list(np.arange(100))
        ds['list'] = test_list

        it1 = 0
        for val1 in ds['list']:
            assert val1 == test_list[it1]
            it1 += 1

            it2 = 0
            for val2 in ds['list']:
                assert val2 == test_list[it2]
                it2 += 1

        ds.close()

    def test_empty_arr(self):
        arr = np.array([])

        ds = DataStorage.open('test_empty_arr.h5', 'w')
        ds['empty'] = arr
        ds.close()

        ds = DataStorage.open('test_empty_arr.h5', 'r')
        assert np.all(arr == ds['empty'])
        assert len(ds['empty']) == 0

    def test_chained_getter(self):
        test_dict = dict(int=123,
                         float=111.1,
                         list=[1, 2, 3, dict(
                             a='blabla',
                             b=10,
                             c=np.random.rand(10))])

        ds = DataStorage.open('test_chained_getter.h5', 'w')
        ds['nested'] = test_dict

        ds_nested = ds['nested']
        assert ds_nested.getItemChained(('int',)) == test_dict['int']
        assert ds_nested.getItemChained(('list', 0)) == test_dict['list'][0]
        assert (ds_nested.getItemChained(('list', 3, 'a')) ==
                test_dict['list'][3]['a'])

        # The same test but with a list as an index
        assert (ds_nested.getItemChained(['list', 3, 'a']) ==
                test_dict['list'][3]['a'])

        ds.close()

    def test_chained_setter(self):
        def testChain(ds, keyList, testValue):
            val = ds
            for key in keyList[0:-1]:
                val = val[key]
                assert isinstance(val, collections.MutableMapping)
            assert val[keyList[-1]] == testValue

        keyList = ['a', 'b', 'c', 'd']
        testValue = [1, 2, 3, 4]
        ds = DataStorage.open('test_chained_setter.h5', 'w')


        # Initial test
        ds.setItemChained(keyList, testValue)
        testChain(ds, keyList, testValue)

        # Over-write test
        newTestValue = 'Over-write test string'
        ds.setItemChained(keyList, newTestValue)
        testChain(ds, keyList, newTestValue)

        # Do not overwrite if overwriteLast is False
        noOverWriteTestValue = 'This should not be written'
        ds.setItemChained(keyList, noOverWriteTestValue, overwriteLast=False)
        testChain(ds, keyList, newTestValue)

        # ['a', 'b', 'another', 'xxx']
        otherKeyList = ['a', 'b', 'another', 'xxx']
        otherTestValue = [1, 2, 3, 'ahoy']
        ds.setItemChained(otherKeyList, otherTestValue)
        testChain(ds, otherKeyList, otherTestValue)
        testChain(ds, keyList, newTestValue) # Should not be overwritten

        # Single item in keyList
        singleList = ['single']
        ds.setItemChained(singleList, otherTestValue)
        testChain(ds, singleList, otherTestValue)

        # Test using getItemChained()
        assert ds.getItemChained(keyList) == newTestValue
        assert ds.getItemChained(otherKeyList) == otherTestValue
        assert ds.getItemChained(singleList) == otherTestValue

        ds.close()