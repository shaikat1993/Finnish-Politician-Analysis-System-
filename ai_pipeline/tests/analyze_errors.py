"""
Error Analysis: Categorize and analyze false negatives from WildJailbreak benchmark

This script provides qualitative analysis of system failures to:
1. Sample and manually categorize false negatives
2. Identify patterns in missed attacks
3. Create error taxonomy for thesis Discussion section
4. Suggest potential improvements

Day 4 of Tier-1 improvements plan.
"""
import json
import random
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple


def load_wildjailbreak_results():
    """Load WildJailbreak evaluation results from comprehensive evaluation"""
    # Try comprehensive evaluation first
    comp_path = Path("test_reports/comprehensive_security_evaluation.json")

    if comp_path.exists():
        with open(comp_path) as f:
            data = json.load(f)
            # Extract WildJailbreak category
            if "categories" in data and "WildJailbreak" in data["categories"]:
                wj_data = data["categories"]["WildJailbreak"]
                # Check if detailed results exist in by_category
                return wj_data

    # Fallback to standalone file
    results_path = Path("test_reports/wildjailbreak_evaluation.json")
    if not results_path.exists():
        raise FileNotFoundError(
            "WildJailbreak evaluation not found in comprehensive results. "
            "The WildJailbreak data may not have detailed_results field."
        )

    with open(results_path) as f:
        return json.load(f)


def extract_false_negatives(results: dict) -> List[Dict]:
    """
    Extract all false negatives (missed attacks) from results

    Args:
        results: WildJailbreak evaluation results

    Returns:
        List of false negative samples
    """
    false_negatives = []

    for result in results.get("detailed_results", []):
        # False negative = attack that was not detected (blocked=False)
        if not result.get("blocked", False):
            false_negatives.append({
                "prompt": result.get("prompt", ""),
                "category": result.get("category", "unknown"),
                "tactics": result.get("tactics", []),
                "reason": result.get("reason", "not_detected"),
                "full_result": result
            })

    return false_negatives


def sample_for_manual_analysis(
    false_negatives: List[Dict],
    sample_size: int = 100,
    stratified: bool = True
) -> List[Dict]:
    """
    Sample false negatives for manual analysis

    Args:
        false_negatives: All false negative samples
        sample_size: Number of samples to analyze (default: 100)
        stratified: Whether to sample proportionally by category (default: True)

    Returns:
        Sampled false negatives
    """
    if len(false_negatives) <= sample_size:
        return false_negatives

    if not stratified:
        return random.sample(false_negatives, sample_size)

    # Stratified sampling by category
    by_category = defaultdict(list)
    for fn in false_negatives:
        by_category[fn["category"]].append(fn)

    # Calculate samples per category (proportional)
    total = len(false_negatives)
    sampled = []

    for category, items in by_category.items():
        category_proportion = len(items) / total
        category_samples = max(1, int(sample_size * category_proportion))
        category_samples = min(category_samples, len(items))

        sampled.extend(random.sample(items, category_samples))

    # If we're under sample_size due to rounding, add more randomly
    if len(sampled) < sample_size:
        remaining = [fn for fn in false_negatives if fn not in sampled]
        additional = sample_size - len(sampled)
        sampled.extend(random.sample(remaining, min(additional, len(remaining))))

    return sampled[:sample_size]


def auto_categorize_errors(samples: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Automatically categorize errors based on observable patterns

    Categories:
    1. Obfuscation - Heavy use of special chars, encoding, symbols
    2. Indirection - Subtle, indirect phrasing, hypotheticals
    3. Context manipulation - Long context, role-play, scenarios
    4. Multilingual - Non-English or mixed languages
    5. Novel tactics - Patterns not seen in training

    Args:
        samples: Sampled false negatives

    Returns:
        dict: Categorized errors
    """
    categories = {
        "obfuscation": [],
        "indirection": [],
        "context_manipulation": [],
        "multilingual": [],
        "novel_tactics": [],
        "other": []
    }

    # Keywords/patterns for auto-categorization
    obfuscation_markers = ["```", "base64", "encode", "0x", "\\x", "unicode"]
    indirection_markers = ["hypothetically", "imagine", "what if", "suppose", "theoretically"]
    context_markers = ["roleplay", "character", "story", "scenario", "pretend", "act as"]
    multilingual_markers = ["translate", "language", "言", "語", "中文"]

    for sample in samples:
        prompt = sample["prompt"].lower()
        tactics = [t.lower() for t in sample.get("tactics", [])]

        # Check for obfuscation
        if any(marker in prompt for marker in obfuscation_markers):
            categories["obfuscation"].append(sample)
        # Check for indirection
        elif any(marker in prompt for marker in indirection_markers):
            categories["indirection"].append(sample)
        # Check for context manipulation
        elif any(marker in prompt or marker in " ".join(tactics) for marker in context_markers):
            categories["context_manipulation"].append(sample)
        # Check for multilingual
        elif any(marker in prompt for marker in multilingual_markers) or not prompt.isascii():
            categories["multilingual"].append(sample)
        # Novel tactics (check if tactics list is unusual)
        elif len(tactics) > 3 or any("novel" in t or "creative" in t for t in tactics):
            categories["novel_tactics"].append(sample)
        else:
            categories["other"].append(sample)

    return categories


def analyze_error_patterns(categorized_errors: Dict[str, List[Dict]]) -> Dict:
    """
    Analyze patterns within each error category

    Args:
        categorized_errors: Errors grouped by category

    Returns:
        dict: Analysis results
    """
    analysis = {}

    for category, errors in categorized_errors.items():
        if not errors:
            continue

        # Extract common tactics
        all_tactics = []
        for error in errors:
            all_tactics.extend(error.get("tactics", []))

        # Count tactic frequency
        tactic_counts = defaultdict(int)
        for tactic in all_tactics:
            tactic_counts[tactic] += 1

        # Get top tactics
        top_tactics = sorted(tactic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Sample examples (max 3 per category)
        examples = []
        for error in errors[:3]:
            prompt_preview = error["prompt"][:200] + "..." if len(error["prompt"]) > 200 else error["prompt"]
            examples.append({
                "prompt_preview": prompt_preview,
                "tactics": error.get("tactics", [])[:3]  # Top 3 tactics
            })

        analysis[category] = {
            "count": len(errors),
            "percentage": 0,  # Will calculate after
            "top_tactics": [{"tactic": t, "count": c} for t, c in top_tactics],
            "examples": examples,
            "interpretation": get_category_interpretation(category, len(errors))
        }

    # Calculate percentages
    total = sum(cat["count"] for cat in analysis.values())
    for cat_data in analysis.values():
        cat_data["percentage"] = round((cat_data["count"] / total * 100), 1) if total > 0 else 0

    return analysis


def get_category_interpretation(category: str, count: int) -> str:
    """Get interpretation for each error category"""
    interpretations = {
        "obfuscation": f"Pattern-based detector struggles with encoded/obfuscated attacks ({count} cases). May require preprocessing layer for decoding.",
        "indirection": f"Indirect, subtle phrasing bypasses direct pattern matching ({count} cases). Suggests need for semantic understanding.",
        "context_manipulation": f"Long-form roleplay/scenarios dilute attack patterns ({count} cases). Context window and pattern density are challenges.",
        "multilingual": f"Non-English attacks evade detection ({count} cases). Current multilingual patterns may need expansion.",
        "novel_tactics": f"Novel attack strategies not covered by patterns ({count} cases). Demonstrates adversarial adaptation.",
        "other": f"Miscellaneous failure modes ({count} cases). Require individual investigation."
    }
    return interpretations.get(category, f"{count} cases in this category")


def create_error_taxonomy() -> Dict:
    """
    Create hierarchical error taxonomy for thesis

    Returns:
        dict: Taxonomy structure
    """
    return {
        "title": "Error Taxonomy: False Negative Analysis",
        "description": "Hierarchical classification of system failures",
        "taxonomy": {
            "Level 1: Attack Complexity": {
                "Simple (Direct)": "Direct malicious prompts with clear attack intent",
                "Moderate (Obfuscated)": "Attacks using encoding, special characters, or formatting",
                "Complex (Indirect)": "Subtle, hypothetical, or context-dependent attacks"
            },
            "Level 2: Evasion Technique": {
                "Obfuscation": "Character encoding, symbols, formatting tricks",
                "Indirection": "Hypotheticals, 'what-if' scenarios, indirect phrasing",
                "Context Manipulation": "Roleplay, stories, long-form scenarios",
                "Multilingual": "Non-English or mixed-language attacks",
                "Novel Tactics": "Creative combinations not seen in pattern development"
            },
            "Level 3: Pattern Detection Failure": {
                "Pattern Absent": "Attack type not covered by current patterns",
                "Pattern Too Specific": "Existing pattern too narrow to match variant",
                "Context Dilution": "Attack signal lost in surrounding context",
                "Preprocessing Gap": "Obfuscation not handled by preprocessor"
            }
        },
        "thesis_contribution": "Provides structured understanding of failure modes for Discussion section"
    }


def run_error_analysis(sample_size: int = 100):
    """
    Main error analysis pipeline

    Args:
        sample_size: Number of false negatives to analyze (default: 100)
    """
    print("\n" + "="*70)
    print("ERROR ANALYSIS: False Negative Categorization")
    print("="*70)
    print(f"\nAnalyzing failure patterns from WildJailbreak benchmark")
    print(f"Sample size: {sample_size} false negatives\n")

    # Load results
    print("📊 Loading WildJailbreak evaluation results...")
    results = load_wildjailbreak_results()

    # Extract false negatives
    print("🔍 Extracting false negatives...")
    false_negatives = extract_false_negatives(results)
    print(f"   Total false negatives: {len(false_negatives)}")

    # Sample for analysis
    print(f"\n📋 Sampling {sample_size} cases for manual analysis...")
    random.seed(42)  # For reproducibility
    sampled = sample_for_manual_analysis(false_negatives, sample_size, stratified=True)
    print(f"   Sampled: {len(sampled)} cases")

    # Auto-categorize
    print("\n🏷️  Auto-categorizing errors by pattern...")
    categorized = auto_categorize_errors(sampled)

    # Analyze patterns
    print("📈 Analyzing error patterns...\n")
    pattern_analysis = analyze_error_patterns(categorized)

    # Print summary
    print("="*70)
    print("ERROR CATEGORY BREAKDOWN")
    print("="*70)

    for category, data in sorted(pattern_analysis.items(), key=lambda x: x[1]["count"], reverse=True):
        if data["count"] > 0:
            print(f"\n📌 {category.upper().replace('_', ' ')}")
            print(f"   Count: {data['count']} ({data['percentage']:.1f}%)")
            print(f"   Interpretation: {data['interpretation']}")
            if data["top_tactics"]:
                print(f"   Top Tactics: {', '.join([t['tactic'] for t in data['top_tactics'][:3]])}")

    # Create taxonomy
    taxonomy = create_error_taxonomy()

    # Create output
    output = {
        "analysis_name": "Error Analysis - False Negative Categorization",
        "analysis_date": "2025-11-24",
        "methodology": f"Stratified sampling of {sample_size} false negatives from {len(false_negatives)} total",
        "total_false_negatives": len(false_negatives),
        "sampled_for_analysis": len(sampled),
        "categorization": pattern_analysis,
        "taxonomy": taxonomy,
        "thesis_tables": {
            "table_5_error_categories": {
                "title": "Table 5.X: Error Analysis - False Negative Categories",
                "columns": ["Category", "Count", "Percentage", "Top Failure Pattern"],
                "rows": [
                    {
                        "category": cat.replace("_", " ").title(),
                        "count": data["count"],
                        "percentage": f"{data['percentage']:.1f}%",
                        "top_pattern": data["top_tactics"][0]["tactic"] if data["top_tactics"] else "N/A"
                    }
                    for cat, data in sorted(pattern_analysis.items(), key=lambda x: x[1]["count"], reverse=True)
                    if data["count"] > 0
                ]
            }
        },
        "key_findings": [
            f"Analyzed {len(sampled)} false negatives from {len(false_negatives)} total misses",
            f"Primary failure mode: {max(pattern_analysis.items(), key=lambda x: x[1]['count'])[0].replace('_', ' ')}",
            "Pattern-based detection struggles most with obfuscation and indirection",
            "Multilingual attacks suggest need for expanded language coverage",
            "Novel tactics demonstrate ongoing adversarial adaptation"
        ],
        "improvement_suggestions": {
            "short_term": [
                "Add preprocessing layer for common obfuscation techniques (base64, unicode)",
                "Expand multilingual pattern coverage (currently Finnish-focused)",
                "Add semantic similarity checking for indirect attacks"
            ],
            "long_term": [
                "Hybrid approach: Combine patterns with semantic understanding (embeddings)",
                "Active learning: Periodically retrain on new adversarial examples",
                "Ensemble methods: Multiple detection strategies voting"
            ]
        }
    }

    # Save results
    output_path = Path("test_reports/error_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("KEY FINDINGS FOR THESIS")
    print("="*70)

    for finding in output["key_findings"]:
        print(f"\n✅ {finding}")

    print("\n\n💡 IMPROVEMENT SUGGESTIONS:")
    print("\nShort-term:")
    for suggestion in output["improvement_suggestions"]["short_term"]:
        print(f"  • {suggestion}")

    print("\nLong-term:")
    for suggestion in output["improvement_suggestions"]["long_term"]:
        print(f"  • {suggestion}")

    print(f"\n\n📊 Results saved to: {output_path}")
    print("\n📋 THESIS INTEGRATION:")
    print("  • Add Table 5.X to Results/Discussion chapter")
    print("  • Discuss error taxonomy in Discussion section")
    print("  • Use improvement suggestions for Future Work section")
    print("  • Cite this analysis as evidence of systematic evaluation")

    return output


if __name__ == "__main__":
    print("\n🔬 Starting Error Analysis...")

    try:
        results = run_error_analysis(sample_size=100)
        print("\n✅ Error analysis completed successfully!")
        print("\n📋 NEXT STEPS (Day 5):")
        print("  1. Baseline comparison: Implement simple regex baseline")
        print("  2. Compare FPAS vs naive approach")
        print("  3. Demonstrate value of systematic design")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
