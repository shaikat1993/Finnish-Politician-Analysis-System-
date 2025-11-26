#!/usr/bin/env python3
"""
Analyze WildJailbreak false negatives to identify patterns for improvement.
"""

import json
import sys
from collections import Counter

def analyze_misses(report_file):
    """Analyze which prompts were missed by PromptGuard."""

    with open(report_file, 'r') as f:
        results = json.load(f)

    print(f"\n{'='*70}")
    print(f" WildJailbreak False Negative Analysis")
    print(f"{'='*70}\n")

    # Extract false negatives (adversarial attacks that weren't detected)
    false_negatives = [
        item for item in results['detailed_results']
        if not item['detected'] and item['data_type'].startswith('adversarial')
    ]

    print(f"Total samples: {results['metadata']['total_samples']}")
    print(f"Detection rate: {results['metrics']['detection_rate_percent']}%")
    print(f"False negatives: {len(false_negatives)}")
    print(f"\n{'='*70}")
    print(f" SAMPLE FALSE NEGATIVES (First 20)")
    print(f"{'='*70}\n")

    # Show first 20 false negatives to identify patterns
    for i, item in enumerate(false_negatives[:20]):
        print(f"\n[{i+1}] Index {item['index']} ({item['data_type']})")
        print(f"Prompt: {item['prompt_snippet']}")
        print(f"---")

    print(f"\n{'='*70}")
    print(f" PATTERN ANALYSIS")
    print(f"{'='*70}\n")

    # Analyze common patterns in missed prompts
    patterns = {
        'role_play': 0,
        'imagine': 0,
        'fictional': 0,
        'pretend': 0,
        'as_a': 0,
        'you_are': 0,
        'research': 0,
        'novel': 0,
        'story': 0,
        'character': 0,
        'scenario': 0,
        'hypothetical': 0,
        'let_us': 0,
        'creative': 0,
    }

    for item in false_negatives:
        snippet = item['prompt_snippet'].lower()
        if 'role' in snippet or 'roleplay' in snippet:
            patterns['role_play'] += 1
        if 'imagine' in snippet:
            patterns['imagine'] += 1
        if 'fictional' in snippet or 'fiction' in snippet:
            patterns['fictional'] += 1
        if 'pretend' in snippet:
            patterns['pretend'] += 1
        if snippet.startswith('as a '):
            patterns['as_a'] += 1
        if 'you are ' in snippet or snippet.startswith('you are'):
            patterns['you_are'] += 1
        if 'research' in snippet:
            patterns['research'] += 1
        if 'novel' in snippet:
            patterns['novel'] += 1
        if 'story' in snippet or 'narrative' in snippet:
            patterns['story'] += 1
        if 'character' in snippet:
            patterns['character'] += 1
        if 'scenario' in snippet:
            patterns['scenario'] += 1
        if 'hypothetical' in snippet:
            patterns['hypothetical'] += 1
        if "let's" in snippet or 'let us' in snippet:
            patterns['let_us'] += 1
        if 'creative' in snippet:
            patterns['creative'] += 1

    print(f"Common patterns in {len(false_negatives)} false negatives:\n")
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / len(false_negatives)) * 100
            print(f"  {pattern:20s}: {count:4d} ({pct:5.1f}%)")

    print(f"\n{'='*70}")
    print(f" RECOMMENDATIONS FOR IMPROVEMENT")
    print(f"{'='*70}\n")

    print("Based on the false negative patterns, consider adding detection for:")
    print("1. Role-playing scenarios ('Imagine you are...', 'You are a...')")
    print("2. Fictional framing ('In a novel/story...', 'fictional scenario')")
    print("3. Creative writing requests ('As a writer...', 'creative exercise')")
    print("4. Research framing ('As a researcher...', 'for research purposes')")
    print("5. Hypothetical scenarios ('In a hypothetical world...', 'imagine a world')")
    print("6. Character-based prompts ('character named X...', 'roleplay as...')")
    print("\nThese are common jailbreak tactics that use indirection to bypass safety.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_wildjailbreak_misses.py <report_file.json>")
        sys.exit(1)

    analyze_misses(sys.argv[1])
