import conff
p = conff.Parser()
r = p.parse('F.template("{{ 1 + 2 }}")')
print(r)