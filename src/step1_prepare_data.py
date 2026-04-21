"""
Step 1: Data Preparation - Sample Selection for Manual Translation and LLM Training

Selects 100 trials using stratified sampling (balanced by trial type).
Creates datasets for:
1. Manual translation (human annotators)
2. LLM training/fine-tuning
"""

import pandas as pd
import numpy as np
import argparse
import json
from pathlib import Path


def load_data(input_path):
    df = pd.read_csv(input_path)
    print(f"✓ Loaded {len(df)} trials\n")
    return df


def analyze_dataset(df):
    print(f"\nTotal trials: {len(df)}")
    
    if 'Legal_Proceeding' in df.columns:
        print("\nDistribution by Legal Proceeding Type:")
        print(df['Legal_Proceeding'].value_counts().head(10))
    
    # Text statistics
    df['word_count'] = df['Trial_Text'].str.split().str.len()
    df['char_count'] = df['Trial_Text'].str.len()
    
    print(f"\nText Statistics:")
    print(f"  Average words per trial: {df['word_count'].mean():.1f}")
    print(f"  Median words per trial: {df['word_count'].median():.1f}")
    print(f"  Min words: {df['word_count'].min()}")
    print(f"  Max words: {df['word_count'].max()}")
    
    print(f"\n  Average characters per trial: {df['char_count'].mean():.1f}")
    print(f"  Median characters per trial: {df['char_count'].median():.1f}")
    
    # Date range
    if 'Date' in df.columns:
        valid_dates = df['Date'].dropna()
        if len(valid_dates) > 0:
            print(f"\nDate range: {valid_dates.min()} to {valid_dates.max()}")
            print(f"Trials with dates: {len(valid_dates)} out of {len(df)}")
    
    return df


def create_stratified_sample(df, sample_size=100, stratify_by='Legal_Proceeding', random_state=42):
    if stratify_by not in df.columns:
        print(f"\nWarning: Column '{stratify_by}' not found. Cannot stratify.")
        return None
    
    print(f"\nStratifying by: {stratify_by}")
    
    # Calculate proportional sample sizes
    value_counts = df[stratify_by].value_counts()
    print(f"\nOriginal distribution:")
    for value, count in value_counts.head(10).items():
        pct = (count / len(df)) * 100
        print(f"  {value}: {count} ({pct:.1f}%)")
    
    # Stratified sampling - proportional to original distribution
    sample_df = df.groupby(stratify_by, group_keys=False).apply(
        lambda x: x.sample(
            n=max(1, int(sample_size * len(x) / len(df))),
            random_state=random_state
        )
    )
    
    # If we don't have enough, add more randomly
    if len(sample_df) < sample_size:
        remaining = sample_size - len(sample_df)
        remaining_df = df[~df.index.isin(sample_df.index)].sample(
            n=remaining, 
            random_state=random_state
        )
        sample_df = pd.concat([sample_df, remaining_df])
    
    # If we have too many, trim randomly
    if len(sample_df) > sample_size:
        sample_df = sample_df.sample(n=sample_size, random_state=random_state)
    
    print(f"\nSample distribution:")
    sample_counts = sample_df[stratify_by].value_counts()
    for value, count in sample_counts.head(10).items():
        pct = (count / len(sample_df)) * 100
        print(f"  {value}: {count} ({pct:.1f}%)")
    
    print(f"\n✓ Selected {len(sample_df)} trials")
    
    return sample_df.reset_index(drop=True)


def save_for_manual_translation(sample_df, output_dir):
    """
    Save sample for manual translation.
    
    Creates a CSV with:
    - Trial metadata
    - Original text
    - Empty columns for manual translation
    """
    print("\n" + "="*80)
    print("SAVING FOR MANUAL TRANSLATION")
    print("="*80)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare manual translation template
    manual_df = sample_df.copy()
    
    # Add translation columns
    manual_df['Modern_Translation'] = ''
    manual_df['Translator_Name'] = ''
    manual_df['Translation_Date'] = ''
    manual_df['Translation_Notes'] = ''
    manual_df['Quality_Score'] = ''  # For self-assessment (1-5)
    
    # Reorder columns
    cols = ['SWP_No', 'Accused_or_Topic', 'Date', 'Legal_Proceeding', 
            'Trial_Text', 'Modern_Translation', 'Translator_Name', 
            'Translation_Date', 'Translation_Notes', 'Quality_Score']
    
    # Only include columns that exist
    cols = [c for c in cols if c in manual_df.columns]
    manual_df = manual_df[cols]
    
    # Save
    output_path = output_dir / 'manual_translation_template.csv'
    manual_df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved manual translation template: {output_path}")
    print(f"  Trials: {len(manual_df)}")
    print(f"  Columns: {', '.join(cols)}")
    
    return output_path


def save_for_llm_training(sample_df, output_dir):
    """
    Save sample for LLM training/fine-tuning.
    
    Creates multiple formats:
    1. JSONL format (for fine-tuning)
    2. CSV format (for general use)
    3. Train/validation split (80/20)
    """
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save full sample as CSV
    csv_path = output_dir / 'llm_training_data.csv'
    sample_df.to_csv(csv_path, index=False)
    print(f"\n✓ Saved CSV: {csv_path}")
    
    # 2. Create train/validation split (80/20)
    train_size = int(0.8 * len(sample_df))
    
    train_df = sample_df.iloc[:train_size]
    val_df = sample_df.iloc[train_size:]
    
    train_path = output_dir / 'llm_training_train.csv'
    val_path = output_dir / 'llm_training_validation.csv'
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    
    print(f"✓ Saved train set: {train_path} ({len(train_df)} trials)")
    print(f"✓ Saved validation set: {val_path} ({len(val_df)} trials)")
    
    # 3. Create JSONL format (for fine-tuning APIs)
    jsonl_path = output_dir / 'llm_training_data.jsonl'
    
    with open(jsonl_path, 'w') as f:
        for _, row in sample_df.iterrows():
            obj = {
                'id': row.get('SWP_No', ''),
                'original_text': row['Trial_Text'],
                'metadata': {
                    'accused': row.get('Accused_or_Topic', ''),
                    'date': row.get('Date', ''),
                    'proceeding': row.get('Legal_Proceeding', '')
                }
            }
            f.write(json.dumps(obj) + '\n')
    
    print(f"✓ Saved JSONL: {jsonl_path}")
    
    # 4. Save metadata
    metadata = {
        'total_samples': len(sample_df),
        'train_samples': len(train_df),
        'validation_samples': len(val_df),
        'split_ratio': '80/20',
        'files': {
            'csv': str(csv_path.name),
            'train': str(train_path.name),
            'validation': str(val_path.name),
            'jsonl': str(jsonl_path.name)
        }
    }
    
    metadata_path = output_dir / 'llm_training_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Saved metadata: {metadata_path}")
    
    return {
        'csv': csv_path,
        'train': train_path,
        'validation': val_path,
        'jsonl': jsonl_path,
        'metadata': metadata_path
    }


def create_summary_stats(sample_df, output_dir):
    """Create summary statistics file."""
    output_dir = Path(output_dir)
    
    stats = {
        'sample_size': len(sample_df),
        'text_statistics': {
            'avg_words': float(sample_df['Trial_Text'].str.split().str.len().mean()),
            'median_words': float(sample_df['Trial_Text'].str.split().str.len().median()),
            'min_words': int(sample_df['Trial_Text'].str.split().str.len().min()),
            'max_words': int(sample_df['Trial_Text'].str.split().str.len().max()),
            'total_words': int(sample_df['Trial_Text'].str.split().str.len().sum())
        }
    }
    
    if 'Legal_Proceeding' in sample_df.columns:
        stats['proceeding_distribution'] = sample_df['Legal_Proceeding'].value_counts().to_dict()
    
    if 'Date' in sample_df.columns:
        valid_dates = sample_df['Date'].dropna()
        if len(valid_dates) > 0:
            stats['date_range'] = {
                'earliest': str(valid_dates.min()),
                'latest': str(valid_dates.max()),
                'count_with_dates': len(valid_dates)
            }
    
    stats_path = output_dir / 'sample_statistics.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n✓ Saved statistics: {stats_path}")
    
    return stats_path


def main():
    parser = argparse.ArgumentParser(
        description='Step 1: Data Preparation - Stratified Sample Selection'
    )
    parser.add_argument('--input', required=True, 
                       help='Input trials CSV file')
    parser.add_argument('--output-dir', default='data/samples', 
                       help='Output directory (default: data/samples)')
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Number of trials to sample (default: 100)')
    parser.add_argument('--random-seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Load data
    df = load_data(args.input)
    
    # Analyze dataset
    df = analyze_dataset(df)
    
    # Create stratified sample
    sample_df = create_stratified_sample(
        df, 
        sample_size=args.sample_size,
        stratify_by='Legal_Proceeding',
        random_state=args.random_seed
    )
    
    if sample_df is None:
        print("\n✗ Failed to create sample")
        return
    
    # Save for manual translation
    manual_path = save_for_manual_translation(sample_df, args.output_dir)
    
    # Save for LLM training
    llm_paths = save_for_llm_training(sample_df, args.output_dir)
    
    # Create summary statistics
    stats_path = create_summary_stats(sample_df, args.output_dir)
    
    # Final summary
    # print("\n" + "="*80)
    # print("STEP 1 COMPLETE!")
    # print("="*80)
    # print(f"\nGenerated files in: {args.output_dir}/")
    # print("\nFor Manual Translation:")
    # print(f"  • manual_translation_template.csv")
    # print("\nFor LLM Training:")
    # print(f"  • llm_training_data.csv (full dataset)")
    # print(f"  • llm_training_train.csv (80% train)")
    # print(f"  • llm_training_validation.csv (20% validation)")
    # print(f"  • llm_training_data.jsonl (JSONL format)")
    # print(f"  • llm_training_metadata.json")
    # print("\nStatistics:")
    # print(f"  • sample_statistics.json")


if __name__ == '__main__':
    main()