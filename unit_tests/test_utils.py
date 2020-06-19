import pytest
from utils import normalize_values, wild_card_to_regex


parameters = [
    ({
        u'Desc': ['5', 4, 'Test', 'TEST'],
        'Column': (3, 'ArRrrR')
    },
     {
        'desc': ['5', 4, 'test', 'test'],
        'column': (3, 'arrrrr')
    }
    ),
    (
        [(1, 'AbbAA', u'CbC'), ({"desc": [1, 'test']})],
        [(1, 'abbaa', 'cbc'), ({"desc": [1, 'test']})]
    ),
    (
        (('AAbbCc', 2), (u'AAbbCc', 2), ('test', 4), (4, 5)),
        (('aabbcc', 2), ('aabbcc', 2), ('test', 4), (4, 5))
    )
]


@pytest.mark.parametrize("test_input,expected", parameters)
def test_normalize_values(test_input, expected):
    assert normalize_values(test_input) == expected


parameters = [
    ({
        u'Desc': ['5', 4, ' Test', ' TEST'],
        'Column': (3, 'ArRrrR')
    },
     {
        'desc': ['5', 4, ' test', ' test'],
        'column': (3, 'arrrrr')
    },
        False,
        None
    ),
    (
        [(1, ' AbbAA ', u' CbC '), ({"desc ": [1, '  test']})],
        [(1, 'abbaa', 'cbc'), ({"desc": [1, 'test']})],
        True,
        None
    ),
    (
        (('AAbbCc', 2), (u'AAbbCc', 2), ('test', 4), (4, 5)),
        (('bbcc', 2), ('bbcc', 2), ('test', 4), (4, 5)),
        True,
        'a'
    ),
    (
        (('  AAb bCc', 2), (u'AAb bCc ', 2), ('  te st', 4), (4, 5)),
        (('b bcc', 2), ('b bcc', 2), ('e s', 4), (4, 5)),
        True,
        [' ', 'a', 't']
    )
]


@pytest.mark.parametrize("test_input,expected,simple_strip,str_strip", parameters)
def test_normalize_values_with_strip(test_input, expected, simple_strip, str_strip):
    assert normalize_values(test_input, simple_strip, str_strip) == expected



