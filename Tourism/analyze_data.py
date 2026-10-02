import json
from collections import Counter

with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count empty fields per model
model_fields = {}
for item in data:
    model = item.get('model', 'unknown')
    if model not in model_fields:
        model_fields[model] = {'total': 0, 'empty_counts': Counter()}
    model_fields[model]['total'] += 1
    fields = item.get('fields', {})
    for key, value in fields.items():
        if value is None or value == '' or value == 0 or value == 0.0 or value == [] or value == {}:
            model_fields[model]['empty_counts'][key] += 1

# Print summary
for model, info in sorted(model_fields.items()):
    print(f"\n{model} ({info['total']} records):")
    for field, count in info['empty_counts'].most_common(10):
        pct = count / info['total'] * 100
        print(f"  {field}: {count} ({pct:.1f}%)")
