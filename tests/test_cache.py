from threading import Thread

from CachedMethods import cached_property, cached_method, cached_args_method, class_cached_property, FrozenDict


class TestFrozenDict:
    def test_mapping(self):
        d = FrozenDict(a=1, b=2)
        assert d['a'] == 1
        assert len(d) == 2
        assert set(d) == {'a', 'b'}

    def test_copy(self):
        d = FrozenDict(x=10)
        c = d.copy()
        assert isinstance(c, dict)
        c['y'] = 20
        assert 'y' not in d

    def test_repr(self):
        d = FrozenDict(a=1)
        assert repr(d) == repr({'a': 1})


class TestCachedProperty:
    def test_basic(self):
        class A:
            call_count = 0

            @cached_property
            def val(self):
                self.call_count += 1
                return 42

        a = A()
        assert a.val == 42
        assert a.val == 42
        assert a.call_count == 1

    def test_freezes_list(self):
        class A:
            @cached_property
            def val(self):
                return [1, 2, 3]

        assert isinstance(A().val, tuple)

    def test_freezes_set(self):
        class A:
            @cached_property
            def val(self):
                return {1, 2}

        assert isinstance(A().val, frozenset)

    def test_freezes_dict(self):
        class A:
            @cached_property
            def val(self):
                return {'a': 1}

        assert isinstance(A().val, FrozenDict)

    def test_delete_resets(self):
        class A:
            call_count = 0

            @cached_property
            def val(self):
                self.call_count += 1
                return self.call_count

        a = A()
        assert a.val == 1
        del a.val
        assert a.val == 2

    def test_private_name(self):
        class A:
            @cached_property
            def __secret(self):
                return 99

        a = A()
        assert a._A__secret == 99

    def test_class_access(self):
        class A:
            @cached_property
            def val(self):
                return 1

        assert isinstance(A.val, cached_property)

    def test_threaded(self):
        class A:
            call_count = 0

            @cached_property
            def val(self):
                self.call_count += 1
                return 42

        a = A()
        results = []

        def reader():
            results.append(a.val)

        threads = [Thread(target=reader) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == 42 for r in results)
        assert a.call_count == 1


class TestCachedMethod:
    def test_basic(self):
        class A:
            call_count = 0

            @cached_method
            def compute(self):
                self.call_count += 1
                return 'result'

        a = A()
        assert a.compute() == 'result'
        assert a.compute() == 'result'
        assert a.call_count == 1

    def test_per_instance(self):
        class A:
            def __init__(self, x):
                self.x = x

            @cached_method
            def compute(self):
                return self.x * 2

        a = A(3)
        b = A(5)
        assert a.compute() == 6
        assert b.compute() == 10

    def test_freezes(self):
        class A:
            @cached_method
            def get_list(self):
                return [1, 2]

            @cached_method
            def get_set(self):
                return {3, 4}

            @cached_method
            def get_dict(self):
                return {'k': 'v'}

        a = A()
        assert isinstance(a.get_list(), tuple)
        assert isinstance(a.get_set(), frozenset)
        assert isinstance(a.get_dict(), FrozenDict)

    def test_threaded(self):
        class A:
            call_count = 0

            @cached_method
            def compute(self):
                self.call_count += 1
                return 99

        a = A()
        results = []

        def reader():
            results.append(a.compute())

        threads = [Thread(target=reader) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == 99 for r in results)
        assert a.call_count == 1


class TestCachedArgsMethod:
    def test_basic(self):
        class A:
            call_count = 0

            @cached_args_method
            def compute(self, x, y):
                self.call_count += 1
                return x + y

        a = A()
        assert a.compute(1, 2) == 3
        assert a.compute(1, 2) == 3
        assert a.compute(3, 4) == 7
        assert a.call_count == 2

    def test_per_instance(self):
        class A:
            def __init__(self, base):
                self.base = base

            @cached_args_method
            def compute(self, x):
                return self.base + x

        a = A(10)
        b = A(20)
        assert a.compute(1) == 11
        assert b.compute(1) == 21

    def test_freezes(self):
        class A:
            @cached_args_method
            def get(self, kind):
                if kind == 'list':
                    return [1]
                elif kind == 'set':
                    return {2}
                else:
                    return {'k': 3}

        a = A()
        assert isinstance(a.get('list'), tuple)
        assert isinstance(a.get('set'), frozenset)
        assert isinstance(a.get('dict'), FrozenDict)

    def test_threaded(self):
        class A:
            call_count = 0

            @cached_args_method
            def compute(self, x):
                self.call_count += 1
                return x * 2

        a = A()
        results = []

        def reader(val):
            results.append(a.compute(val))

        threads = [Thread(target=reader, args=(i % 5,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == (i % 5) * 2 for i, r in enumerate(results))
        assert a.call_count == 5


class TestClassCachedProperty:
    def test_basic(self):
        class A:
            __class_cache__ = {}
            call_count = 0

            @class_cached_property
            def val(self):
                A.call_count += 1
                return 'shared'

        a1 = A()
        a2 = A()
        assert a1.val == 'shared'
        assert a2.val == 'shared'
        assert A.call_count == 1

    def test_subclass_isolation(self):
        class A:
            __class_cache__ = {}

            @class_cached_property
            def val(self):
                return type(self).__name__

        class B(A):
            pass

        assert A().val == 'A'
        assert B().val == 'B'

    def test_freezes(self):
        class A:
            __class_cache__ = {}

            @class_cached_property
            def val(self):
                return [1, 2, 3]

        assert isinstance(A().val, tuple)

    def test_class_access(self):
        class A:
            __class_cache__ = {}

            @class_cached_property
            def val(self):
                return 1

        assert isinstance(A.val, class_cached_property)

    def test_threaded(self):
        class A:
            __class_cache__ = {}
            call_count = 0

            @class_cached_property
            def val(self):
                A.call_count += 1
                return 'shared'

        results = []

        def reader():
            results.append(A().val)

        threads = [Thread(target=reader) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == 'shared' for r in results)
        assert A.call_count == 1
