import unittest

from parser import AlexsonParser
from syntax_tree import Boolean, Number, String, Variable, Null, BlockNode, Root

# 以下测试用例取自《远行星号》游戏真实数据文件（game data/），
# 用于验证解析器在实际游戏文件格式下的正确性。


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

    def test_parse_string_with_backslash(self):
        # JSON 源文本 "\\" 应解析为含单个反斜杠的字符串，to_alexson() 应还原为 "\\"
        node = AlexsonParser('"\\\\"').parse_value()
        self.assertEqual(node, String('\\'))
        self.assertEqual(node.to_alexson(), '"\\\\"')

    def test_parse_string_roundtrip_backslash_in_object(self):
        # 确保含反斜杠的字符串在对象中也能正确还原
        string = '{"path":"C:\\\\Users\\\\foo"}'
        root = AlexsonParser(string).parse()
        self.assertEqual(root['path'], String('C:\\Users\\foo'))
        self.assertEqual(root.to_alexson(), string)

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

    # -------------------------------------------------------------------------
    # 真实游戏文件测试用例
    # -------------------------------------------------------------------------

    def test_battle_objectives_roundtrip(self):
        """
        来源：game data/data/config/battle_objectives.json（截取前两条）
        特征：tab缩进、trailing comma、纯标准JSON结构（无注释/变量）
        验证：解析后 to_alexson() 完全还原原始文本
        """
        string = (
            '{\n'
            '\t"nav_buoy":{\n'
            '\t\t"name":"Nav Buoy",\n'
            '\t\t"captureTime":10,\n'
            '\t\t"battleSizeFractionBonus":0.05,\n'
            '\t},\n'
            '\t"sensor_array":{\n'
            '\t\t"name":"Sensor Jammer",\n'
            '\t\t"captureTime":10,\n'
            '\t\t"battleSizeFractionBonus":0.05,\n'
            '\t},\n'
            '}'
        )
        root = AlexsonParser(string).parse()
        self.assertEqual(root.to_alexson(), string)

    def test_battle_objectives_translate(self):
        """
        来源：game data/data/config/battle_objectives.json
        验证：修改 name 字段后格式完全保留
        """
        string = (
            '{\n'
            '\t"nav_buoy":{\n'
            '\t\t"name":"Nav Buoy",\n'
            '\t\t"captureTime":10,\n'
            '\t},\n'
            '\t"comm_relay":{\n'
            '\t\t"name":"Comm Relay",\n'
            '\t\t"captureTime":10,\n'
            '\t},\n'
            '}'
        )
        root = AlexsonParser(string).parse()
        root['nav_buoy']['name'] = String('导航浮标')
        root['comm_relay']['name'] = String('通讯中继站')

        expected = (
            '{\n'
            '\t"nav_buoy":{\n'
            '\t\t"name":"导航浮标",\n'
            '\t\t"captureTime":10,\n'
            '\t},\n'
            '\t"comm_relay":{\n'
            '\t\t"name":"通讯中继站",\n'
            '\t\t"captureTime":10,\n'
            '\t},\n'
            '}'
        )
        self.assertEqual(root.to_alexson(), expected)

    def test_custom_entities_variable_in_array(self):
        """
        来源：game data/data/config/custom_entities.json
        特征：数组中包含无引号变量值（STATIONS），行内注释，trailing comma
        验证：Variable 节点不加引号输出，注释/格式完整保留
        """
        string = (
            '{\n'
            '\t"nav_buoy":{\n'
            '\t\t"baseId":"base_campaign_objective",\n'
            '\t\t"defaultName":"Nav Buoy", # used if name=null in addCustomEntity()\n'
            '\t\t"tags":["nav_buoy", "neutrino_high", "objective"],\n'
            '\t\t"layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayers.java for possible values\n'
            '\t},\n'
            '}'
        )
        root = AlexsonParser(string).parse()
        # 格式完整还原
        self.assertEqual(root.to_alexson(), string)
        # Variable 节点值正确
        self.assertEqual(root['nav_buoy']['layers'][0], Variable('STATIONS'))

    def test_custom_entities_translate_preserves_variable_and_comment(self):
        """
        来源：game data/data/config/custom_entities.json
        验证：翻译 defaultName 后，Variable 和注释均不受影响
        """
        string = (
            '{\n'
            '\t"nav_buoy":{\n'
            '\t\t"defaultName":"Nav Buoy", # used if name=null in addCustomEntity()\n'
            '\t\t"layers":[STATIONS], # what layer(s) to render in.\n'
            '\t},\n'
            '}'
        )
        root = AlexsonParser(string).parse()
        root['nav_buoy']['defaultName'] = String('导航浮标')

        expected = (
            '{\n'
            '\t"nav_buoy":{\n'
            '\t\t"defaultName":"导航浮标", # used if name=null in addCustomEntity()\n'
            '\t\t"layers":[STATIONS], # what layer(s) to render in.\n'
            '\t},\n'
            '}'
        )
        self.assertEqual(root.to_alexson(), expected)

    def test_planets_commented_out_line(self):
        """
        来源：game data/data/config/planets.json（nebula_center_average 条目）
        特征：行内注释（值后带 #），以及整行被注释掉的键值对（#"key":"value"）
        验证：两种注释形式均能正确解析和还原
        """
        string = (
            '{\n'
            '\t"nebula_center_average":{\n'
            '\t\t"name":"Nebula",\n'
            '\t\t"tilt":0, # left-right (>0 tilts to the left)\n'
            '\t\t"isStar":true,\n'
            '\t\t#"starscapeIcon":"graphics/backgrounds/star1.png",\n'
            '\t\t"isNebulaCenter":true,\n'
            '\t},\n'
            '}'
        )
        root = AlexsonParser(string).parse()
        self.assertEqual(root.to_alexson(), string)

    def test_planets_translate_preserves_commented_line(self):
        """
        来源：game data/data/config/planets.json
        验证：翻译 name 字段后，被注释掉的整行原样保留
        """
        string = (
            '{\n'
            '\t"nebula_center_average":{\n'
            '\t\t"name":"Nebula",\n'
            '\t\t"tilt":0, # left-right (>0 tilts to the left)\n'
            '\t\t#"starscapeIcon":"graphics/backgrounds/star1.png",\n'
            '\t\t"isNebulaCenter":true,\n'
            '\t},\n'
            '}'
        )
        root = AlexsonParser(string).parse()
        root['nebula_center_average']['name'] = String('星云')

        expected = (
            '{\n'
            '\t"nebula_center_average":{\n'
            '\t\t"name":"星云",\n'
            '\t\t"tilt":0, # left-right (>0 tilts to the left)\n'
            '\t\t#"starscapeIcon":"graphics/backgrounds/star1.png",\n'
            '\t\t"isNebulaCenter":true,\n'
            '\t},\n'
            '}'
        )
        self.assertEqual(root.to_alexson(), expected)
