import pandas as pd
from yargy import rule, Parser, or_
from yargy.predicates import eq, gram


# Загрузим данные, из полного диалга оставим только реплики менеджера
data = pd.read_csv('test_data.csv')
data_text_manager = data[data['role'] == 'manager']
data_text_manager['text'] = data_text_manager['text'].apply(lambda x: x.lower())


# Создадим правила для извлечения реплик
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
parser_start = Parser(START_DLG)
parser_end = Parser(END_DLG)
parser_named = Parser(NAMED)
parser_company = Parser(NAME_COMPANY)


# Функция ищет список совпадений и возвращает последнее совпадение
def search(parser, row):
    q = []
    for match in parser.findall(row):
        q.append([x.value for x in match.tokens])
        return q[-1]


# Функция из списка слов собирает в одну фразу
def join_text(row):
    if row != 0:
        return ' '.join(row)
    else:
        return row


# Создаем новые колонки, где менеджер здоровается, представляется, называет компанию, прощается
data_text_manager['start_dlg'] = data_text_manager['text'].apply(lambda x: search(parser_start, x))
data_text_manager['end_dlg'] = data_text_manager['text'].apply(lambda x: search(parser_end, x))
data_text_manager['named_dlg'] = data_text_manager['text'].apply(lambda x: search(parser_named, x))
data_text_manager['company'] = data_text_manager['text'].apply(lambda x: search(parser_company, x))
# Заменяем пропуски на 0
data_text_manager = data_text_manager.fillna(0)


# Оставляем строки только с указанными выше фразами
data_text_manager = data_text_manager[(data_text_manager['start_dlg'] != 0) |
                                     (data_text_manager['end_dlg'] != 0) |
                                     (data_text_manager['named_dlg'] != 0) |
                                     (data_text_manager['company'] != 0)]


# Функция удаляет слова 'компании' и 'компания'
def del_word(row):
    if row != 0 and 'компании' in row:
        row.remove('компании')
    elif row != 0 and 'компания' in row:
        row.remove('компания')
    else:
        pass
    return row


# Применяем фунцию del_word к колонке company
data_text_manager['company'] = data_text_manager['company'].apply(del_word)


# Применяем функцию join_text к новым колонкам
columns = ['start_dlg', 'end_dlg', 'named_dlg', 'company']
for column in columns:
    data_text_manager[column] = data_text_manager[column].apply(join_text)


# Функция ищет имя в колонке
def parser_name(row):
    if row != 0:
        for match in Parser(rule(NAME)).findall(row):
            q = [x.value for x in match.tokens][0]
        return q
    else:
        return 0


# Применяем функцию к фразе, где менеджер представился
data_text_manager['name_manager'] = data_text_manager['named_dlg'].apply(parser_name)

# Создаем результирующую таблицу
columns = ['dlg_id', 'start_dlg', 'named_dlg', 'name_manager', 'company', 'end_dlg']
df = pd.DataFrame(columns=columns)
df['dlg_id'] = data['dlg_id'].unique()

for column in columns[1:]:
    for i in df['dlg_id']:
        if len(data_text_manager[(data_text_manager['dlg_id'] == i) &
                                 (data_text_manager[column] != 0)][column]) > 0:
            # выражение - ненулевой срез данных для конкретного диалога и конкретной колонки
            df[column][i] = data_text_manager[(data_text_manager['dlg_id'] == i) &
                                              (data_text_manager[column] != 0)][column].values[-1]
        else:
            df[column][i] = '-'


# Последний шаг - проверка менеджера на приветствие и прощание
def test_manager(row):
    if row['start_dlg'] != '-' and row['end_dlg'] != '-':
        return '+'
    else:
        return '-'


df['test_manager'] = df.apply(test_manager, axis=1)
df.to_csv('df_parser.csv')
print(df)