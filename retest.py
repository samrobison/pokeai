import re
a = """Spinda L83
HP: 100.0% (235/235)
Ability: Contrary / Item: Focus Sash
147 Atk / 147 Def / 147 SpA / 147 SpD / 104 Spe
• Return
• Trick Room
• Superpower
• Sucker Punch"""

parsed = re.search("((?:[\\w-]+\\s?){1,2})(?:\\([\\w\\s-]+\\))?\\sL(\\d+)\\nHP:\\s100\\.0%\\s\\((\\d+)\\/+\\d+\\)\\nAbility:\\s([\\w\\s-]+)\\/\\sItem:\\s([\\w\\s]+)\\n(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\s\\/\\s(\\d+)\\s\\w+\\n..(['\\w\\s-]+)\\n..(['\\w\\s-]+)\\n..(['\\w\\s-]+)\\n..(['\\w\\s]+)", a)

print(parsed.groups())

a = """Vikavolt L81
HP: 100%
Possible abilities: Levitate
74 to 116 Spe (before items/abilities/modifiers)"""

parsed = re.search("((?:[\\w]+\\s?){1,2})(?:\\([\\w\\s-]+\\))?\\sL(\\d+)\\nHP:\\s100%\\n(?:Ability|Possible abilities):\\s(?:[,\\w\\s-]+)\\n(\\d+)\\sto\\s(\\d+)", a)

print(parsed.groups())
