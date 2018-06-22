def makecomplete(fnfields):
    def f(text, line, begidx, endix):
        tks = tokens(text, line, begidx, endix)
        tkpos = len(tks) - 1
        if text.strip() == '':
            tkpos += 1
        if tkpos >= len(fnfields):
            return []
        else:
            return fnfields[tkpos](text)
    return f
    

def tokens(text, line, begidx, endix):
    return line[:begidx].split()

def choice(text, choices):
    return [x for x in choices if x.startswith(text)]

def booleancmp(text):
    return choice(text,['==',
                        '!='])

def zeroone(text):
    return choice(text,['0',
                        '1'])

def boolean(text):
    return choice(text,['True',
                        'False'])

def numbercmp(text):
    return choice(text,['==',
                        '!=',
                        '>',
                        '<',
                        '>=',
                        '<=',
                    ])
def strcmp(text):
    return choice(text,['==',
                        '!=',
                        'startswith',
                        'contains',
                        'endswith',
                    ])

def validdate(y,m,d):
    if m in [2,4,6,9,11] and d in [31]:
        return False
    if m in [2] and d in [30, 31]:
        return False
    if m in [2] and d in [29]:
        if y%4!=0:
            return False
        if y%100==0 and y%400!=0:
            return False
    return True

dates = ['{0:4}-{1:02}-{2:02}'.format(y,m,d)
         for y in range(2000,2021)
         for m in range(1,13)
         for d in range(1,32) if validdate(y,m,d)]

def date(text):
    return choice(text,dates)

hours = ['{0}:{1}:{2}'.format(y,m,d)
         for y in range(0,25)
         for m in range(0,60)
         for d in range(0,60)]

def hour(text):
    return choice(text,hours)

