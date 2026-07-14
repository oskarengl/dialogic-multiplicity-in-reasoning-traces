import json
import random

def load_debates(filepath):
    debates = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            debates.append(json.loads(line))
    return debates

def main():
    filepath = 'c:/bachelor research/.1 recent approach/data/archive/ai_debate/regenerated_ai_debate.jsonl'
    
    print("Loading debates...")
    debates = load_debates(filepath)
    print(f"Loaded {len(debates)} debates\n")
    
    # Sample 100 random debates
    sample = random.sample(debates, min(100, len(debates)))
    
    # Save to file with UTF-8 encoding
    with open('c:/bachelor research/.1 recent approach/scripts/last_turns_sample.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("LAST TURN ANALYSIS (100 SAMPLED DEBATES)\n")
        f.write("="*80 + "\n")
        
        for i, debate in enumerate(sample):
            turns = debate['turns']
            last_turn = turns[-1]['text_clean']
            
            f.write(f"\n{'='*80}\n")
            f.write(f"Debate {i+1}: {debate['source_item_id']}\n")
            f.write(f"Numbers: {debate['puzzle']['numbers']}\n")
            f.write(f"Total turns: {len(turns)}\n")
            f.write(f"{'='*80}\n")
            f.write("Last turn text:\n")
            f.write(last_turn)
            f.write("\n")
    
    print("Saved last turns to last_turns_sample.txt")

if __name__ == '__main__':
    main()
