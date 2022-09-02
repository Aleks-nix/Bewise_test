import pandas as pd
from yargy.tokenizer import MorphTokenizer
from yargy import rule, Parser, or_
from yargy.predicates import eq, gram

# Загрузим данные, из полного диалга оставим только реплики менеджера
data = pd.read_csv('test_data.csv')
data_text_manager = data[data['role'] == 'manager']

# Создадим список, в котором один элемент списка - это все реплики менеджера за один диалог
text = []
for id in data_text_manager['dlg_id'].unique():
    df = data_text_manager[data_text_manager['dlg_id'] == id]
    a = ''
    for i in df.index:
        a = a + " ; " + df['text'].loc[i]
    text.append(a)

text = [x.lower() for x in text]

# Создадим правила для извлечения реплик
#bИзвлечем необходимые реплики и проведем проверку менеджера на обязательное приветствие и прощание

NOUN = gram('NOUN')
NAME = gram('Name')

START_DLG = or_(
    rule(eq('здравствуйте')),
    rule(eq('добрый'), eq('день')),
    rule(eq('приветствую')),
    rule(eq('привет')),
    rule(eq('здрасте'))
)

END_DLG = or_(
    rule(eq('до'), eq('свидания')),
    rule(eq('досвидания')),
    rule(eq('всего'), eq('доброго')),
    rule(eq('хорошего'), eq('дня')),
    rule(eq('прекрасного'), eq('дня')),
    rule(eq('пока')),
    rule(eq('всего'), eq('хорошего'))
)
NAMED = or_(
    rule(eq('меня'), eq('зовут'), NAME),
    rule(eq('меня'), NAME, eq('зовут')),
    rule(eq('это'),NAME)
)
NAME_COMPANY = or_(
    rule(eq('компания'), NAME.repeatable()),
    rule(eq('компании'), NAME.repeatable()),
    rule(eq('компания'), NOUN.repeatable()),
    rule(eq('компании'), NOUN.repeatable())
)
parser = Parser(or_(START_DLG, END_DLG, NAMED, NAME_COMPANY))
parser_start = Parser(START_DLG)
parser_end = Parser(END_DLG)

for i in range(len(text)):
    test = []
    start = []
    end = []
    print(i, 'dlg_id')
    for match in parser.findall(text[i]):
        test.append([x.value for x in match.tokens])
    print(test)
    for match in parser_start.findall(text[i]):
        start.append([x.value for x in match.tokens])
    for match in parser_end.findall(text[i]):
        end.append([x.value for x in match.tokens])
    if len(start) != 0 and len(end) != 0:
        print('Проверка пройдена!')
    else:
        print('ПРОВАЛ')
    print()