import json
import re

def check_debate(index):
    line = open('c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl', 'r', encoding='utf-8').readlines()[index]
    data = json.loads(line)
    text = data['full_text_no_labels']
    numbers = data['puzzle']['numbers']
    
    # Extract boxed expressions
    boxed_pattern = r'\\boxed\{([^}]+)\}'
    matches = re.findall(boxed_pattern, text)
    
    print(f'Index {index}: {data["source_item_id"]}')
    print(f'Numbers: {numbers}')
    print(f'Boxed expressions found: {len(matches)}')
    
    for expr in matches:
        cleaned = expr.strip()
        cleaned = re.sub(r'\s*=\s*24\s*$', '', cleaned)
        cleaned = re.sub(r'\s*=\s*24\s*[,.!?]*$', '', cleaned)
        try:
            cleaned = cleaned.replace('\\frac', '').replace('{', '(').replace('}', ')')
            cleaned = cleaned.replace('\\times', '*').replace('\\div', '/')
            cleaned = cleaned.replace('\\cdot', '*')
            cleaned = cleaned.replace('\\left', '').replace('\\right', '')
            result = eval(cleaned)
            is_24 = abs(result-24) < 0.001
            print(f'  {expr[:60]}... -> {result:.2f} (is 24: {is_24})')
        except Exception as e:
            print(f'  {expr[:60]}... -> ERROR: {str(e)[:30]}')
    print()

# Check the 20 random indices
indices = [445, 94, 102, 427, 254, 332, 442, 311, 79, 188, 448, 381, 534, 115, 560, 146, 468, 517, 460, 29]

for i in indices:
    check_debate(i)
