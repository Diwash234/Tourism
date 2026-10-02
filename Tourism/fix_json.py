import json

with open('data.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last complete object by finding the last '},' or '}'
last_complete = content.rfind('},')
if last_complete > 0:
    fixed = content[:last_complete+1] + ']\n'
    try:
        data = json.loads(fixed)
        print(f'Fixed JSON is valid! {len(data)} records')
        with open('data.json', 'w', encoding='utf-8') as f:
            f.write(fixed)
        print('File saved successfully')
    except json.JSONDecodeError as e:
        print(f'JSON still invalid: {e}')
else:
    print('No complete object found')
