"""
Text Standardization Script for Game of 24 Datasets

Applies uniform character set, LaTeX standardization, and text normalization
across all datasets while preserving mathematical content.

Creates *_processed.jsonl files alongside originals.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Define allowed character set
ALLOWED_CHARS = set(
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789'
    '.,!?;:\'"()-[]{}'
    '+-*/=<>&×÷^_'
    ' \n'
)

# Mathematical symbols to preserve
MATH_SYMBOLS = {'×', '÷', '+', '-', '*', '/', '=', '<', '>', '^', '_'}

# Speaker label patterns
SPEAKER_PATTERNS = [
    r'^[A-Z][a-z]+:\s*',  # "Speaker: "
    r'^[A-Z][a-z]+\s+[A-Z][a-z]+:\s*',  # "First Last: "
    r'^Speaker\s+[A-Z]:\s*',  # "Speaker A: "
    r'^Speaker\s+\d+:\s*',  # "Speaker 1: "
    r'^[A-Z][a-z]+\s+\d+:\s*',  # "Speaker 123: "
    r'^[A-Z]+:\s*',  # Any all-caps word followed by colon (catch more cases)
]

# Animal names from human debate
ANIMAL_NAMES = [
    'Cat', 'Dog', 'Bird', 'Fish', 'Fox', 'Owl', 'Bear', 'Wolf', 'Lion', 'Tiger',
    'Elephant', 'Giraffe', 'Zebra', 'Hippo', 'Rabbit', 'Deer', 'Monkey', 'Panda',
    'Koala', 'Kangaroo', 'Penguin', 'Dolphin', 'Whale', 'Eagle', 'Hawk', 'Falcon',
    'Parrot', 'Peacock', 'Flamingo', 'Swan', 'Duck', 'Goose', 'Chicken', 'Rooster'
]


def extract_system_line(text: str) -> Tuple[str, str]:
    """
    Extract SYSTEM line from transcript.
    Returns (system_info, transcript_without_system)
    """
    system_match = re.search(r'^SYSTEM:\s*(.+?)(?:\n|$)', text, re.MULTILINE)
    if system_match:
        system_info = system_match.group(1).strip()
        transcript = text.replace(system_match.group(0), '').strip()
        return system_info, transcript
    return None, text


def remove_speaker_labels(text: str) -> Tuple[str, int]:
    """
    Remove speaker labels from transcript.
    Returns (cleaned_text, labels_removed_count)
    """
    cleaned = text
    labels_removed = 0
    
    # Remove standard speaker patterns
    for pattern in SPEAKER_PATTERNS:
        matches = re.findall(pattern, cleaned, re.MULTILINE)
        labels_removed += len(matches)
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
    
    # Remove animal names
    for animal in ANIMAL_NAMES:
        pattern = rf'^{animal}:\s*'
        matches = re.findall(pattern, cleaned, re.MULTILINE)
        labels_removed += len(matches)
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)
        
        # Remove self-references
        pattern = rf'I agree with {animal}'
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        labels_removed += len(matches)
        cleaned = re.sub(pattern, 'I agree', cleaned, flags=re.IGNORECASE)
    
    return cleaned, labels_removed


def standardize_latex(text: str) -> Tuple[str, int]:
    """
    Convert LaTeX to standardized plain text.
    Returns (cleaned_text, conversions_count)
    """
    cleaned = text
    conversions = 0
    
    # \frac{a}{b} → (a/b)
    frac_matches = re.findall(r'\\frac\{([^}]+)\}\{([^}]+)\}', cleaned)
    conversions += len(frac_matches)
    cleaned = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1/\2)', cleaned)
    
    # \times → ×
    times_matches = re.findall(r'\\times', cleaned)
    conversions += len(times_matches)
    cleaned = re.sub(r'\\times', '×', cleaned)
    
    # \sqrt{x} → sqrt(x)
    sqrt_matches = re.findall(r'\\sqrt\{([^}]+)\}', cleaned)
    conversions += len(sqrt_matches)
    cleaned = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', cleaned)
    
    # Remove display math delimiters
    cleaned = re.sub(r'\\\[', '', cleaned)
    cleaned = re.sub(r'\\\]', '', cleaned)
    cleaned = re.sub(r'\\\(', '', cleaned)
    cleaned = re.sub(r'\\\)', '', cleaned)
    
    # Keep exponents and subscripts but remove braces
    cleaned = re.sub(r'\^\{([^}]+)\}', r'^\1', cleaned)
    cleaned = re.sub(r'_\{([^}]+)\}', r'_\1', cleaned)
    
    # Remove LaTeX sizing/ boxing commands and leftover curly braces
    # (curly braces are not part of actual Game of 24 math notation)
    cleaned = re.sub(r'boxed', '', cleaned)
    cleaned = re.sub(r'left\(', '(', cleaned)
    cleaned = re.sub(r'right\)', ')', cleaned)
    cleaned = cleaned.replace('{', '').replace('}', '')
    
    return cleaned, conversions


def filter_character_set(text: str) -> Tuple[str, int, List[str]]:
    """
    Filter to allowed character set only.
    Returns (filtered_text, chars_removed_count, removed_chars_list)
    """
    filtered = []
    removed = []
    removed_chars = set()
    
    for char in text:
        if char in ALLOWED_CHARS:
            filtered.append(char)
        else:
            removed.append(char)
            removed_chars.add(char)
    
    return ''.join(filtered), len(removed), sorted(list(removed_chars))


def normalize_text(text: str) -> Tuple[str, int]:
    """
    Normalize quotes, whitespace, and special characters.
    Returns (normalized_text, changes_count)
    """
    cleaned = text
    changes = 0
    
    # Quote standardization: convert curly quotes and backtick to straight quotes.
    # Using explicit Unicode escapes to avoid accidental literal interpretation.
    curly_quotes = {"\u2018", "\u2019", "\u201c", "\u201d", "\u0060"}  # ' ' " " `
    for quote in curly_quotes:
        if quote in cleaned:
            changes += cleaned.count(quote)
            cleaned = cleaned.replace(quote, "'" if quote in {"\u2018", "\u2019", "\u0060"} else '"')
    
    # Remove emojis and special unicode
    emoji_pattern = re.compile(
        '['
        '\U0001F600-\U0001F64F'  # emoticons
        '\U0001F300-\U0001F5FF'  # symbols & pictographs
        '\U0001F680-\U0001F6FF'  # transport & map symbols
        '\U0001F1E0-\U0001F1FF'  # flags
        '\U00002702-\U000027B0'  # dingbats
        '\U000024C2-\U0001F251'  # enclosed characters
        ']+', 
        flags=re.UNICODE
    )
    emoji_matches = emoji_pattern.findall(cleaned)
    changes += len(emoji_matches)
    cleaned = emoji_pattern.sub('', cleaned)
    
    # Remove special punctuation
    special_punct = ['¿', '…', '—', '–', '、', '。']
    for punct in special_punct:
        if punct in cleaned:
            changes += cleaned.count(punct)
            cleaned = cleaned.replace(punct, '')
    
    # Collapse multiple spaces
    space_matches = re.findall(r' {2,}', cleaned)
    changes += len(space_matches)
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    
    # Remove leading/trailing whitespace from lines
    lines = cleaned.split('\n')
    cleaned_lines = [line.strip() for line in lines]
    cleaned = '\n'.join(cleaned_lines)
    
    # Remove excessive newlines
    newline_matches = re.findall(r'\n{3,}', cleaned)
    changes += len(newline_matches)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip(), changes


def process_transcript(text: str, is_debate: bool = False) -> Dict:
    """
    Process a transcript through all standardization steps.
    Returns processing_info dict with all changes.
    """
    original_length = len(text)
    processing_info = {
        'original_length': original_length,
        'processed_length': 0,
        'characters_removed': 0,
        'latex_conversions': 0,
        'speaker_labels_removed': 0,
        'system_extracted': False,
        'removed_char_types': [],
        'processing_timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    current_text = text
    
    # Step 1: Extract SYSTEM line (for debates)
    if is_debate:
        system_info, current_text = extract_system_line(current_text)
        if system_info:
            processing_info['system_extracted'] = True
            processing_info['system_info'] = system_info
    
    # Step 2: Remove speaker labels (for debates)
    if is_debate:
        current_text, labels_removed = remove_speaker_labels(current_text)
        processing_info['speaker_labels_removed'] = labels_removed
    
    # Step 3: LaTeX standardization
    current_text, latex_conversions = standardize_latex(current_text)
    processing_info['latex_conversions'] = latex_conversions
    
    # Step 4: Character set filtering
    current_text, chars_removed, removed_char_types = filter_character_set(current_text)
    processing_info['characters_removed'] = chars_removed
    processing_info['removed_char_types'] = removed_char_types
    
    # Step 5: Text normalization
    current_text, normalization_changes = normalize_text(current_text)
    processing_info['normalization_changes'] = normalization_changes
    
    # Calculate final processed length after all transformations
    processing_info['processed_length'] = len(current_text)
    
    return {
        'processed_text': current_text,
        'processing_info': processing_info,
        'system_info': processing_info.get('system_info')
    }


def process_dataset(input_path: Path, output_path: Path, text_field: str, is_debate: bool = False):
    """
    Process an entire dataset file.
    """
    print(f"\nProcessing: {input_path.name}")
    print(f"  Text field: {text_field}")
    print(f"  Is debate: {is_debate}")
    
    processed_rows = []
    total_chars_removed = 0
    total_latex_conversions = 0
    total_speaker_labels_removed = 0
    total_system_extracted = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                text = data.get(text_field, '')
                
                if not text:
                    print(f"  Warning: Empty {text_field} in line {line_num}")
                    continue
                
                # Process the text
                result = process_transcript(text, is_debate=is_debate)
                
                # Update the data
                data[text_field] = result['processed_text']
                data['processing_info'] = result['processing_info']
                
                # Add system_info field if extracted
                if result['system_info']:
                    data['system_info'] = result['system_info']
                
                processed_rows.append(data)
                
                # Track statistics
                total_chars_removed += result['processing_info']['characters_removed']
                total_latex_conversions += result['processing_info']['latex_conversions']
                total_speaker_labels_removed += result['processing_info']['speaker_labels_removed']
                if result['processing_info']['system_extracted']:
                    total_system_extracted += 1
                    
            except json.JSONDecodeError as e:
                print(f"  Error: JSON decode error in line {line_num}: {e}")
            except Exception as e:
                print(f"  Error: Processing error in line {line_num}: {e}")
    
    # Write processed data
    with open(output_path, 'w', encoding='utf-8') as f:
        for row in processed_rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    
    # Print statistics
    print(f"  Processed {len(processed_rows)} rows")
    print(f"  Total characters removed: {total_chars_removed:,}")
    print(f"  Total LaTeX conversions: {total_latex_conversions:,}")
    print(f"  Total speaker labels removed: {total_speaker_labels_removed:,}")
    print(f"  Total SYSTEM lines extracted: {total_system_extracted}")
    print(f"  Output: {output_path.name}")
    
    return len(processed_rows)


def main():
    """Main processing function."""
    base_path = Path(__file__).resolve().parent.parent / 'data'
    human_debate_path = base_path / 'human_debate' / 'unprocessed' / 'delidata_source'

    # Define datasets to process
    datasets = [
        # (input_path, output_path, text_field, is_debate)
        (base_path / 'ai_debate' / 'unprocessed' / 'regenerated_ai_debate.jsonl', base_path / 'ai_debate' / 'processed_ai_debate.jsonl', 'full_text_no_labels', True),
        (base_path / 'ai_monologue' / 'unprocessed' / 'prompted_ai_monologue.jsonl', base_path / 'ai_monologue' / 'processed_prompted_ai_monologue.jsonl', 'transcript', False),
        (base_path / 'ai_reasoning' / 'unprocessed' / 'native_reasoning_traces.jsonl', base_path / 'ai_reasoning' / 'processed_native_reasoning_traces.jsonl', 'think_trace', False),
        (base_path / 'human_debate' / 'unprocessed' / 'human_debate_with_speaker_labels.jsonl', base_path / 'human_debate' / 'processed_human_debate.jsonl', 'transcript', True),
        (base_path / 'human_monologue' / 'unprocessed' / 'human_think_aloud_full.jsonl', base_path / 'human_monologue' / 'unprocessed' / 'processed_think_aloud_full_variant.jsonl', 'think_trace', False),
    ]
    
    print("=" * 60)
    print("Text Standardization for Game of 24 Datasets")
    print("=" * 60)
    
    total_processed = 0
    for input_path, output_path, text_field, is_debate in datasets:
        if not input_path.exists():
            print(f"\nSkipping {input_path.name}: File not found")
            continue
            
        rows_processed = process_dataset(input_path, output_path, text_field, is_debate)
        total_processed += rows_processed
    
    print("\n" + "=" * 60)
    print(f"Total rows processed across all datasets: {total_processed:,}")
    print("=" * 60)


if __name__ == "__main__":
    main()