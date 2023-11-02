# Alexson

Warning: WIP, not ready for use.

A python library for manipulating formatted json data, while preserving the formatting.

## Example

```python
from parser import AlexsonParser
from syntax_tree import String

string = ('{\n'
              '    "nav_buoy": {\n'
              '        "baseId": "base_campaign \\"_objective",\n'
              '        "defaultName":"Nav Buoy", # used if name=null in addCustomEntity() \n'
              '        "tags":["nav_buoy", "neutrino_high", "objective"],\n'
              '        "layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayer for possible values\n'
              '    }\n'
              '}')

root = AlexsonParser(string).parse()

root['nav_buoy']['defaultName'] = String('导航浮标')
print(root)
```

Output:

```json
{
    "nav_buoy": {
        "baseId": "base_campaign \"_objective",
        "defaultName":"导航浮标", # used if name=null in addCustomEntity() 
        "tags":["nav_buoy", "neutrino_high", "objective"],
        "layers":[STATIONS], # what layer(s) to render in. See CampaignEngineLayer for possible values
    }
}
```