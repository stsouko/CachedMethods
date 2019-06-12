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
from functools import wraps


class cached_property:
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.func = func
        self.name = func.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.name] = self.func(obj)
        return value


def cached_method(func):
    """
    cache methods without arguments
    """
    name = f'_cached_method_{func.__name__}'

    @wraps(func)
    def wrapper(self):
        try:
            return self.__dict__[name]
        except KeyError:
            value = self.__dict__[name] = func(self)
            return value
    return wrapper


def cached_args_method(func):
    """
    cache methods results with hashable args
    """
    name = f'_cached_args_method_{func.__name__}'

    @wraps(func)
    def wrapper(self, *args):
        try:
            cache = self.__dict__[name]
        except KeyError:
            value = func(self, *args)
            self.__dict__[name] = {args: value}
            return value
        try:
            return cache[args]
        except KeyError:
            value = cache[args] = func(self, *args)
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
        self.name = func.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        try:
            class_cache = cls.__class_cache__[cls]  # for subclasses isolation
        except KeyError:
            value = self.func(obj)
            cls.__class_cache__[cls] = {self.name: value}
        else:
            try:
                value = class_cache[self.name]
            except KeyError:  # another property or cleaned cache
                value = class_cache[self.name] = self.func(obj)

        try:  # cache in object if possible
            obj.__dict__[self.name] = value
        except AttributeError:
            pass
        return value


__all__ = ['cached_property', 'cached_method', 'cached_args_method', 'class_cached_property']
