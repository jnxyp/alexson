import unittest

from parser import AlexsonParser
from syntax_tree import Boolean, Number, String, Variable, Null, BlockNode, Root


class TestParser(unittest.TestCase):
    def test_parse_boolean_1(self):
        parser = AlexsonParser('true')
        node = parser.parse_value()
        self.assertEqual(node, Boolean(True))

    def test_parse_boolean_2(self):
        parser = AlexsonParser('false')
        node = parser.parse_value()
        self.assertEqual(node, Boolean(False))

    def test_parse_number(self):
        parser = AlexsonParser('1234')
        node = parser.parse_value()
        self.assertEqual(node, Number(1234))

    def test_parse_number_with_decimal(self):
        parser = AlexsonParser('1234.5678')
        node = parser.parse_value()
        self.assertEqual(node, Number(1234.5678))

    def test_parse_string(self):
        parser = AlexsonParser('"I say hello world "')
        node = parser.parse_value()
        self.assertEqual(node, String('I say hello world '))

    def test_parse_string_with_escape(self):
        parser = AlexsonParser('"I say \\"hello world\\""')
        node = parser.parse_value()
        self.assertEqual(node, String('I say "hello world"'))

    def test_parse_variable(self):
        parser = AlexsonParser('STATIONS')
        node = parser.parse_value()
        self.assertEqual(node, Variable('STATIONS'))

    def test_parse_null(self):
        parser = AlexsonParser('null')
        node = parser.parse_value()
        self.assertEqual(node, Null())

    def test_parse_empty(self):
        parser = AlexsonParser('')
        node = parser.parse()
        self.assertEqual(node, Root())

    def test_parse_array(self):
        parser = AlexsonParser('[1, 2.00, 3.1415926, "4", true, false, null]')
        node = parser._parse_array()

        self.assertEqual(node.to_alexson(), '[1, 2.00, 3.1415926, "4", true, false, null]')

        self.assertEqual(node[0], Number(1))
        self.assertEqual(node[-1], Null())

    def test_parse_object(self):
        parser = AlexsonParser('{"a": 1, "b": 2.00, "c": 3.1415926, "d": "4", "e": true, "f": false, "g": null}')
        node = parser._parse_obj()
        self.assertEqual(node.to_alexson(),
                         '{"a": 1, "b": 2.00, "c": 3.1415926, "d": "4", "e": true, "f": false, "g": null}')

        self.assertEqual(node['a'], Number(1))
        self.assertEqual(node['b'], Number(2.00))

        node['b'] = Number("3.00")
        self.assertEqual(node['b'], Number("3.00"))
        self.assertEqual(node.to_alexson(),
                         '{"a": 1, "b": 3.00, "c": 3.1415926, "d": "4", "e": true, "f": false, "g": null}')

    def test_parser(self):
        string = ('{\n'
                  '    "nav_buoy": {\n'
                  '        "baseId": "base_campaign \\"_objective",\n'
                  '        "defaultName":"Nav Buoy", # used if name=null in addCustomEntity() \n'
                  '        "tags":["nav_buoy", "neutrino_high", "objective"],\n'
                  '        "layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayers.java for possible values\n'
                  '    }\n'
                  '}')

        parser = AlexsonParser(string)
        node = parser.parse()
        self.assertEqual(node.to_alexson(), string)

        node['nav_buoy']['defaultName'] = String('导航浮标')

        string_trans = ('{\n'
                        '    "nav_buoy": {\n'
                        '        "baseId": "base_campaign \\"_objective",\n'
                        '        "defaultName":"导航浮标", # used if name=null in addCustomEntity() \n'
                        '        "tags":["nav_buoy", "neutrino_high", "objective"],\n'
                        '        "layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayers.java for possible values\n'
                        '    }\n'
                        '}')
        self.assertEqual(node.to_alexson(), string_trans)
