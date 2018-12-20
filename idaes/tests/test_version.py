"""
Tests for versioning
"""
# third-party
import pytest
# pkg
import idaes
from idaes import ver


def test_idaes_version():
    assert idaes.__version__


def test_ver_class():
    v = ver.Version(1, 2, 3)
    assert str(v) == '1.2.3'
    v = ver.Version(1, 2, 3, 'beta', 1)
    assert str(v) == '1.2.3b1'
    pytest.raises(ValueError, ver.Version, 1, 2, 3, 'howdy')


class MyVersionedClass(ver.HasVersion):
    def __init__(self):
        super(MyVersionedClass, self).__init__(1, 2, 3)


def test_has_version():
    x = MyVersionedClass()
    assert x.version
