"""
Extract exact parameters from Chinese-contaminated debates for regeneration.

This script only extracts parameters - no regeneration logic.
"""
import json
import re
from pathlib import Path

def has_chinese(text):
    """Check if text contains Chinese characters."""
    for char in text:
        code_point = ord(char)
        if 0x4E00 <= code_point <= 0x9FFF:  # CJK Unified Ideographs
            return True
        if char in '，。：；？！「」『（）【】':  # Chinese punctuation
            return True
    return False

def extract_debate_parameters(debate_data):
    """Extract the parameters needed for regeneration."""
    debate_id = debate_data.get('debate_id', '')
    
    # Parse debate_id to get rank and pass
    # Format: g24_XXXX_pY where XXXX is rank, Y is pass (1-3)
    match = re.match(r'g24_(\d+)_p(\d)', debate_id)
    if not match:
        return None
    
    rank = int(match.group(1))
    pass_num = int(match.group(2))
    
    return {
        'debate_id': debate_id,
        'rank': rank,
        'pass': pass_num,
        'turn_order_seed': debate_data.get('turn_order_seed'),
        'source_item_id': debate_data.get('source_item_id'),
        'puzzle_numbers': debate_data.get('puzzle', {}).get('numbers', []),
        'model_version': debate_data.get('model_version'),
        'temperature': debate_data.get('temperature'),
        'max_tokens': debate_data.get('max_tokens')
    }

# Main extraction
filepath = Path(r'C:\bachelor research\.1 recent approach\data\archive\ai_debate\original_chinese_ai_debate.jsonl')

chinese_debates = []
with open(filepath, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            text = data.get('full_text_no_labels', '')
            
            if has_chinese(text):
                params = extract_debate_parameters(data)
                if params:
                    chinese_debates.append(params)
        except:
            continue

# Group by pass for organized regeneration
pass_1 = [d for d in chinese_debates if d['pass'] == 1]
pass_2 = [d for d in chinese_debates if d['pass'] == 2]
pass_3 = [d for d in chinese_debates if d['pass'] == 3]

print("Chinese Debate Parameters for Regeneration")
print("=" * 60)
print(f"Total debates to regenerate: {len(chinese_debates)}")
print(f"  Pass 1: {len(pass_1)}")
print(f"  Pass 2: {len(pass_2)}")
print(f"  Pass 3: {len(pass_3)}")

print("\nParameters by pass:")
print("\nPass 1:")
for debate in sorted(pass_1, key=lambda x: x['rank']):
    print(f"  Rank {debate['rank']:4d}: {debate['debate_id']} (seed: {debate['turn_order_seed']})")

print("\nPass 2:")
for debate in sorted(pass_2, key=lambda x: x['rank']):
    print(f"  Rank {debate['rank']:4d}: {debate['debate_id']} (seed: {debate['turn_order_seed']})")

print("\nPass 3:")
for debate in sorted(pass_3, key=lambda x: x['rank']):
    print(f"  Rank {debate['rank']:4d}: {debate['debate_id']} (seed: {debate['turn_order_seed']})")

# Save to file for reference
output_file = Path(r'C:\bachelor research\.1 recent approach\data\archive\documentation\diagnostics\chinese_debate_parameters.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(chinese_debates, f, indent=2)

print(f"\nParameters saved to: {output_file}")

# Show the command needed for regeneration
all_ranks = sorted(set(d['rank'] for d in chinese_debates))
print(f"\nRanks to regenerate: {all_ranks}")
print(f"Command to regenerate (using original script):")
print(f"  python cell3_build_dataset_random_discussion.py --start {min(all_ranks)} --end {max(all_ranks)} --seed 12345")