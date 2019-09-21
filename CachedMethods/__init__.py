# -*- coding: utf-8 -*-
#
#  Copyright 2019 Ramil Nugmanov <stsouko@live.ru>
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


class cached_property:
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func
        name = func.__name__
        if name.startswith('__') and not name.endswith('__'):
            name = f'_{func.__qualname__.split(".")[-2]}{name}'
        self.name = name

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self.func(obj)
        if isinstance(value, list):
            value = tuple(value)
        elif isinstance(value, set):
            value = frozenset(value)
        elif isinstance(value, dict):
            value = FrozenDict(value)
        obj.__dict__[self.name] = value
        return value


def cached_method(func):
    """
    cache methods without arguments
    """
    name = f'__cached_method_{func.__name__}'

    @wraps(func)
    def wrapper(self):
        try:
            return self.__dict__[name]
        except KeyError:
            value = func(self)
            if isinstance(value, list):
                value = tuple(value)
            elif isinstance(value, set):
                value = frozenset(value)
            elif isinstance(value, dict):
                value = FrozenDict(value)
            self.__dict__[name] = value
            return value
    return wrapper


def cached_args_method(func):
    """
    cache methods results with hashable args
    """
    name = f'__cached_args_method_{func.__name__}'

    @wraps(func)
    def wrapper(self, *args):
        try:
            cache = self.__dict__[name]
        except KeyError:
            value = func(self, *args)
            if isinstance(value, list):
                value = tuple(value)
            elif isinstance(value, set):
                value = frozenset(value)
            elif isinstance(value, dict):
                value = FrozenDict(value)
            self.__dict__[name] = {args: value}
            return value
        try:
            return cache[args]
        except KeyError:
            value = func(self, *args)
            if isinstance(value, list):
                value = tuple(value)
            elif isinstance(value, set):
                value = frozenset(value)
            elif isinstance(value, dict):
                value = FrozenDict(value)
            cache[args] = value
            return value
    return wrapper


class class_cached_property:
    """
    cache property result in class level. usable for dynamic class attrs calculation.

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
        name = func.__name__
        if name.startswith('__') and not name.endswith('__'):
            name = f'_{func.__qualname__.split(".")[-2]}{name}'
        self.name = name

    def __get__(self, obj, cls):
        if obj is None:
            return self
        try:
            class_cache = cls.__class_cache__[cls]  # for subclasses isolation
        except KeyError:
            value = self.func(obj)
            if isinstance(value, list):
                value = tuple(value)
            elif isinstance(value, set):
                value = frozenset(value)
            elif isinstance(value, dict):
                value = FrozenDict(value)
            cls.__class_cache__[cls] = {self.name: value}
        else:
            try:
                value = class_cache[self.name]
            except KeyError:  # another property or cleaned cache
                value = self.func(obj)
                if isinstance(value, list):
                    value = tuple(value)
                elif isinstance(value, set):
                    value = frozenset(value)
                elif isinstance(value, dict):
                    value = FrozenDict(value)
                class_cache[self.name] = value

        try:  # cache in object if possible
            obj.__dict__[self.name] = value
        except AttributeError:
            pass
        return value


__all__ = ['cached_property', 'cached_method', 'cached_args_method', 'class_cached_property', 'FrozenDict']
