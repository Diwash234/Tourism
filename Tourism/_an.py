import io, re, sys
sys.stdout.reconfigure(encoding="utf-8")

s = io.open('test_run.txt', encoding='utf-8', errors='replace').read()
blocks = re.split(r'\n={20,}\n', s)

for b in blocks:
    m = re.search(r'^(FAIL|ERROR): (\S+)', b, re.M)
    if not m:
        continue
    name = m.group(2)
    frames = re.findall(r'File "([^"]+)", line (\d+), in (\S+)', b)
    where = ''
    for path, line, fn in frames:
        if 'Chatbot' in path and 'Lib\\site-packages' not in path \
                and 'django\\' not in path and 'rest_framework\\' not in path:
            where = f'{path.split("Chatbot")[-1]}:{line} {fn}'
            break
    # last assertion / exception
    tail = [l.strip() for l in b.splitlines() if l.strip()]
    exc = ''
    for l in reversed(tail):
        if re.match(r'^[A-Za-z_.]*(Error|Exception|Failed)', l) or l.startswith('AssertionError'):
            exc = l[:100]
            break
    print(f'{name}\n    {where}\n    {exc}\n')