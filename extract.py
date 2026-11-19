"""Extract one checkpoint's answers from a team doc exported as markdown."""
import re, sys, json
CH_NAMES = ['Таргет в соцсетях','Короткие видео','Креаторы и блогеры','Поисковая реклама','Telegram-чаты и каналы','SEO и контент','AI-поиск (GEO)','Сообщество и хакатоны','Партнёрства и платформы','Продажи','Engineering as marketing и open source','Ивенты и выступления']
CH_IDS = ['social','shorts','creators','search','telegram','seo','geo','community','partners','sales','eam','events']
def clean(s):
    s = re.sub(r'\\(.)', r'\1', s); s = s.replace('**', '').replace('<br>', ' ').strip()
    return s
def money(s):
    s = clean(s).lower().replace(' ', '').replace(' ', '').replace(',', '.').replace('$', '')
    if not s: return 0
    m = re.search(r'(\d+(?:\.\d+)?)(k|к|тыс|m|м|млн)?', s)
    if not m: return 0
    v = float(m.group(1)); u = m.group(2) or ''
    if u in ('k', 'к', 'тыс'): v *= 1000
    elif u in ('m', 'м', 'млн'): v *= 1e6
    elif v < 1000 and ('k' in s or 'к' in s): v *= 1000
    return round(v)
def tables(block):
    out, cur = [], []
    for line in block.split('\n'):
        if line.startswith('|'):
            cells = [clean(c) for c in line.strip().strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', c.replace(' ', '')) for c in cells if c): continue
            cur.append(cells)
        elif cur:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out
def section(md, n):
    m = re.search(r'^# \*\*Чекпоинт ' + str(n) + r'.*?$(.*?)(?=^# \*\*)', md, re.S | re.M)
    return m.group(1) if m else ''
def extract(md, n):
    r = {}
    m = re.search(r'Наша компания:\*\*[ \t]*(.*)', md)
    r['company'] = clean(m.group(1)) if m else ''
    sec = section(md, n)
    for t in tables(sec):
        head = t[0]
        body = t[1:]
        if head[:2] == ['Поле', 'Кто']:
            for row in body:
                q, a = row[0], row[-1] if len(row) > 3 else ''
                key = None
                for k, pat in [('positioning','Позиционирование'),('ad','Главная реклама'),('ad_visual','Реклама: что на картинке'),('h1','Первый экран сайта: заголовок'),('h2cta','подзаголовок и текст кнопки'),('announce','Публичное заявление'),('icp','ICP'),('war','Тип войны'),('custom','Своё действие'),('deal','Сделка с другой командой'),('mna','Покупка компании'),('target','Против кого ходим'),('threat','Что он сделал'),('counter','Что делаем в ответ'),('learned','Что сработало'),('change','Что меняем')]:
                    if pat in q: key = k; break
                if key: r[key] = a
        elif head[:2] == ['Тариф', 'Цена в месяц']:
            r['plans'] = [dict(name=row[0], price=(0 if re.search(r'беспл|free|^\$?0$', row[1].lower()) else money(row[1])), what=row[2] if len(row) > 2 else '') for row in body if row[0] or row[1]]
        elif head[0] == 'Канал':
            sp = {}
            for row in body:
                if row[0] in CH_NAMES and money(row[-1]) > 0: sp[CH_IDS[CH_NAMES.index(row[0])]] = money(row[-1])
            r['spend'] = sp
        elif head[0] == 'Карточка':
            r['actions'] = [dict(card=row[0], params=row[1] if len(row) > 1 else '', cost=row[2] if len(row) > 2 else '') for row in body if row[0]]
        elif head[0] == 'Показатель':
            r['econ'] = {row[0][:30]: row[1] for row in body if len(row) > 1 and row[1]}
    return r
if __name__ == '__main__':
    md = open(sys.argv[1]).read(); n = int(sys.argv[2])
    print(json.dumps(extract(md, n), ensure_ascii=False, indent=1))
