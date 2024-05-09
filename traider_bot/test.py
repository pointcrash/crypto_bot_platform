a = dict()
a['psn'] = dict()
a['psna'] = dict()
a['psn']['1'] = 45
a['psn']['2'] = 45
a['psn']['3'] = 45
a['psna']['3'] = 45
a.pop('psn')
for i in a:
    print(i)