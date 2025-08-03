#!/usr/bin/env python3
"""
Quality Filter Presets for SyncNet Processing
Provides different quality filtering presets for different use cases
"""

import argparse
import subprocess
import sys

# Define quality filter presets
FILTER_PRESETS = {
    'strict': {
        'min_confidence': 6.0,
        'max_abs_offset': 2,
        'description': 'Strict filtering - only highest quality chunks (publication ready)'
    },
    'high': {
        'min_confidence': 4.0,
        'max_abs_offset': 5,
        'description': 'High quality filtering - good for training data'
    },
    'medium': {
        'min_confidence': 2.5,
        'max_abs_offset': 8,
        'description': 'Medium quality filtering - balanced approach'
    },
    'relaxed': {
        'min_confidence': 1.5,
        'max_abs_offset': 12,
        'description': 'Relaxed filtering - keep most usable chunks'
    },
    'none': {
        'min_confidence': 0.0,
        'max_abs_offset': 50,
        'description': 'No filtering - keep all chunks with faces'
    }
}

def run_with_preset(input_video, output_base_dir, preset_name, **kwargs):
    """Run processing with a specific quality preset"""
    
    if preset_name not in FILTER_PRESETS:
        print(f"❌ Unknown preset: {preset_name}")
        print(f"Available presets: {', '.join(FILTER_PRESETS.keys())}")
        return False
    
    preset = FILTER_PRESETS[preset_name]
    
    print(f"🎯 Using '{preset_name}' preset")
    print(f"📝 {preset['description']}")
    print(f"🔧 Filters: confidence≥{preset['min_confidence']}, |offset|≤{preset['max_abs_offset']}")
    
    # Build command
    cmd_parts = [
        'python', 'process_long_video.py',
        '--input_video', f'"{input_video}"',
        '--output_dir', f'"{output_base_dir}_{preset_name}"',
        '--min_confidence', str(preset['min_confidence']),
        '--max_abs_offset', str(preset['max_abs_offset'])
    ]
    
    # Add additional arguments
    for key, value in kwargs.items():
        if key in ['chunk_duration', 'overlap', 'min_track', 'min_face_size']:
            cmd_parts.extend([f'--{key}', str(value)])
    
    # Disable filtering for 'none' preset
    if preset_name == 'none':
        cmd_parts.append('--no_filter')
    
    command = ' '.join(cmd_parts)
    
    print(f"\n🚀 Running: {command}")
    result = subprocess.run(command, shell=True)
    
    return result.returncode == 0

def compare_presets(input_video, base_output_dir, presets_to_test):
    """Run multiple presets and compare results"""
    
    print(f"🔍 TESTING MULTIPLE QUALITY PRESETS")
    print("="*60)
    
    results = {}
    
    for preset_name in presets_to_test:
        print(f"\n{'='*40}")
        print(f"Testing preset: {preset_name}")
        print(f"{'='*40}")
        
        success = run_with_preset(input_video, base_output_dir, preset_name)
        
        if success:
            # Try to load results
            import json
            import os
            
            summary_file = f"{base_output_dir}_{preset_name}/processing_summary.json"
            
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                
                results[preset_name] = {
                    'total_chunks': summary['total_chunks'],
                    'successful_analysis': summary['successful_analysis'],
                    'accepted_chunks': len(summary.get('accepted_chunks', [])),
                    'acceptance_rate': summary.get('acceptance_rate', 0),
                    'preset_config': FILTER_PRESETS[preset_name]
                }
                
                print(f"✅ {preset_name}: {results[preset_name]['accepted_chunks']} chunks accepted ({results[preset_name]['acceptance_rate']:.1f}%)")
            else:
                print(f"⚠️  {preset_name}: Results file not found")
        else:
            print(f"❌ {preset_name}: Processing failed")
    
    # Print comparison summary
    if results:
        print(f"\n📊 PRESET COMPARISON SUMMARY")
        print("="*60)
        print(f"{'Preset':<10} {'Confidence':<11} {'Max Offset':<10} {'Accepted':<8} {'Rate':<6}")
        print("-" * 50)
        
        for preset_name, data in results.items():
            config = data['preset_config']
            print(f"{preset_name:<10} ≥{config['min_confidence']:<10} ≤{config['max_abs_offset']:<9} {data['accepted_chunks']:<8} {data['acceptance_rate']:<5.1f}%")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-"*40)
        
        best_balance = None
        best_score = 0
        
        for preset_name, data in results.items():
            # Score based on acceptance rate and absolute number
            score = data['acceptance_rate'] * 0.7 + data['accepted_chunks'] * 0.3
            if score > best_score:
                best_score = score
                best_balance = preset_name
        
        if best_balance:
            print(f"🏆 Best balanced preset: '{best_balance}'")
            print(f"   - {results[best_balance]['accepted_chunks']} high-quality chunks")
            print(f"   - {results[best_balance]['acceptance_rate']:.1f}% acceptance rate")
        
        # Usage recommendations
        highest_acceptance = max(results.values(), key=lambda x: x['acceptance_rate'])
        most_chunks = max(results.values(), key=lambda x: x['accepted_chunks'])
        
        print(f"\n🎯 USAGE RECOMMENDATIONS:")
        print(f"   - For maximum data: Use preset with {most_chunks['accepted_chunks']} chunks")
        print(f"   - For best quality: Use preset with {highest_acceptance['acceptance_rate']:.1f}% acceptance")
        print(f"   - For training: Consider 'high' or 'medium' presets")
        print(f"   - For research: Consider 'strict' preset")

def main():
    parser = argparse.ArgumentParser(description='Process video with quality filter presets')
    parser.add_argument('--input_video', type=str, help='Path to input video file')
    parser.add_argument('--output_dir', type=str, help='Base output directory')
    parser.add_argument('--preset', type=str, choices=list(FILTER_PRESETS.keys()), 
                       help='Quality filter preset to use')
    parser.add_argument('--compare_presets', nargs='+', choices=list(FILTER_PRESETS.keys()),
                       help='Compare multiple presets')
    parser.add_argument('--list_presets', action='store_true', help='List available presets')
    parser.add_argument('--chunk_duration', type=int, default=30, help='Chunk duration in seconds')
    parser.add_argument('--overlap', type=int, default=5, help='Overlap between chunks in seconds')
    
    args = parser.parse_args()
    
    if args.list_presets:
        print("🎯 AVAILABLE QUALITY PRESETS")
        print("="*50)
        for name, config in FILTER_PRESETS.items():
            print(f"\n'{name}':")
            print(f"  {config['description']}")
            print(f"  Min confidence: {config['min_confidence']}")
            print(f"  Max |offset|: {config['max_abs_offset']} frames")
        return 0
    
    if not args.input_video:
        print("❌ --input_video is required (unless using --list_presets)")
        return 1
    
    if not args.output_dir:
        print("❌ --output_dir is required (unless using --list_presets)")
        return 1
    
    if args.compare_presets:
        compare_presets(args.input_video, args.output_dir, args.compare_presets)
    elif args.preset:
        run_with_preset(
            args.input_video, 
            args.output_dir, 
            args.preset,
            chunk_duration=args.chunk_duration,
            overlap=args.overlap
        )
    else:
        print("❌ Either --preset or --compare_presets must be specified")
        print("Use --list_presets to see available options")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
