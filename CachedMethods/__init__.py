# -*- coding: utf-8 -*-
#
#  Copyright 2019-2026 Ramil Nugmanov <stsouko@live.ru>
#  This file is part of CachedMethods.
#
#  CachedMethods is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from collections.abc import Mapping
from functools import wraps
from threading import Lock


_SENTINEL = object()


def _freeze(value):
    if isinstance(value, list):
        return tuple(value)
    elif isinstance(value, set):
        return frozenset(value)
    elif isinstance(value, dict):
        return FrozenDict(value)
    return value


class FrozenDict(Mapping):
    """
    unmutable dict
    """
    __slots__ = '__d'

    def __init__(self, *args, **kwargs):
        self.__d = dict(*args, **kwargs)

    def __iter__(self):
        return iter(self.__d)

    def __len__(self):
        return len(self.__d)

    def __getitem__(self, key):
        return self.__d[key]

    def __repr__(self):
        return repr(self.__d)

    def copy(self):
        """mutable copy of dict"""
        return self.__d.copy()


class cached_property:
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Thread-safe for Python 3.14+ free-threaded (no-GIL) builds.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func
        self.lock = Lock()
        name = func.__name__
        if name.startswith('__') and not name.endswith('__'):
            name = f'_{func.__qualname__.split(".")[-2]}{name}'
        self.name = name

    def __get__(self, obj, cls):
        if obj is None:
            return self
        # Fast path: check without lock
        value = obj.__dict__.get(self.name, _SENTINEL)
        if value is not _SENTINEL:
            return value
        with self.lock:
            # Double-check after acquiring lock
            value = obj.__dict__.get(self.name, _SENTINEL)
            if value is not _SENTINEL:
                return value
            value = _freeze(self.func(obj))
            obj.__dict__[self.name] = value
            return value


def cached_method(func):
    """
    cache methods without arguments.
    Thread-safe for Python 3.14+ free-threaded (no-GIL) builds.
    """
    name = f'__cached_method_{func.__name__}'
    lock_name = f'__cached_method_lock_{func.__name__}'

    @wraps(func)
    def wrapper(self):
        # Fast path: check without lock
        value = self.__dict__.get(name, _SENTINEL)
        if value is not _SENTINEL:
            return value
        # Get or create per-instance lock
        lock = self.__dict__.setdefault(lock_name, Lock())
        with lock:
            # Double-check after acquiring lock
            value = self.__dict__.get(name, _SENTINEL)
            if value is not _SENTINEL:
                return value
            value = _freeze(func(self))
            self.__dict__[name] = value
            return value
    return wrapper


def cached_args_method(func):
    """
    cache methods results with hashable args.
    Thread-safe for Python 3.14+ free-threaded (no-GIL) builds.
    """
    name = f'__cached_args_method_{func.__name__}'
    lock_name = f'__cached_args_method_lock_{func.__name__}'

    @wraps(func)
    def wrapper(self, *args):
        # Fast path: check without lock
        cache = self.__dict__.get(name)
        if cache is not None:
            value = cache.get(args, _SENTINEL)
            if value is not _SENTINEL:
                return value
        # Get or create per-instance lock
        lock = self.__dict__.setdefault(lock_name, Lock())
        with lock:
            # Double-check after acquiring lock
            cache = self.__dict__.get(name)
            if cache is not None:
                value = cache.get(args, _SENTINEL)
                if value is not _SENTINEL:
                    return value
            else:
                cache = {}
                self.__dict__[name] = cache
            value = _freeze(func(self, *args))
            cache[args] = value
            return value
    return wrapper


class class_cached_property:
    """
    cache property result in class level. usable for dynamic class attrs calculation.
    Thread-safe for Python 3.14+ free-threaded (no-GIL) builds.

    required __class_cache__ dict attr:

    class X:
        __class_cache__ = {}

        @class_cached_property
        def my_attr(self):
            return sth
    """
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func
        self.lock = Lock()
        name = func.__name__
        if name.startswith('__') and not name.endswith('__'):
            name = f'_{func.__qualname__.split(".")[-2]}{name}'
        self.name = name

    def __get__(self, obj, cls):
        if obj is None:
            return self
        # Fast path: check instance dict (skipped for slotted classes)
        obj_dict = getattr(obj, '__dict__', None)
        if obj_dict is not None:
            value = obj_dict.get(self.name, _SENTINEL)
            if value is not _SENTINEL:
                return value
        # Check class cache without lock
        class_cache = cls.__class_cache__.get(cls)
        if class_cache is not None:
            value = class_cache.get(self.name, _SENTINEL)
            if value is not _SENTINEL:
                if obj_dict is not None:
                    obj_dict[self.name] = value
                return value
        with self.lock:
            # Double-check class cache after acquiring lock
            class_cache = cls.__class_cache__.get(cls)
            if class_cache is not None:
                value = class_cache.get(self.name, _SENTINEL)
                if value is not _SENTINEL:
                    if obj_dict is not None:
                        obj_dict[self.name] = value
                    return value
            else:
                class_cache = {}
                cls.__class_cache__[cls] = class_cache

            value = _freeze(self.func(obj))
            class_cache[self.name] = value
            if obj_dict is not None:
                obj_dict[self.name] = value
            return value


__all__ = ['cached_property', 'cached_method', 'cached_args_method', 'class_cached_property', 'FrozenDict']
