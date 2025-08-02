#!/usr/bin/env python3
"""
Quality Filtering Comparison Script
Compare results before and after quality filtering
"""

import os
import json
import argparse

def load_summary(summary_file):
    """Load processing summary JSON file"""
    with open(summary_file, 'r') as f:
        return json.load(f)

def compare_filtering_results(unfiltered_summary, filtered_summary):
    """Compare unfiltered vs filtered results"""
    
    print("🔍 QUALITY FILTERING COMPARISON")
    print("="*60)
    
    # Basic stats comparison
    print("📊 BASIC STATISTICS")
    print("-"*40)
    print(f"Total chunks: {unfiltered_summary['total_chunks']}")
    print(f"Successful analysis: {unfiltered_summary['successful_analysis']}")
    print(f"No faces detected: {unfiltered_summary['no_faces_chunks']}")
    
    # Filtering comparison
    if 'accepted_chunks' in filtered_summary:
        print(f"\n🎯 FILTERING RESULTS")
        print("-"*40)
        print(f"Before filtering: {unfiltered_summary['successful_analysis']} usable chunks")
        print(f"After filtering: {len(filtered_summary['accepted_chunks'])} high-quality chunks")
        print(f"Acceptance rate: {filtered_summary['acceptance_rate']:.1f}%")
        print(f"Rejected: {len(filtered_summary['rejected_chunks'])} chunks")
        
        # Quality improvement
        unfiltered_results = [r for r in unfiltered_summary['results'] if r['status'] == 'success']
        filtered_results = [r for r in filtered_summary['results'] if r.get('quality_status') == 'accepted']
        
        if unfiltered_results and filtered_results:
            unfiltered_avg_conf = sum(r['confidence'] for r in unfiltered_results) / len(unfiltered_results)
            filtered_avg_conf = sum(r['confidence'] for r in filtered_results) / len(filtered_results)
            
            unfiltered_avg_offset = sum(abs(r['offset']) for r in unfiltered_results) / len(unfiltered_results)
            filtered_avg_offset = sum(abs(r['offset']) for r in filtered_results) / len(filtered_results)
            
            print(f"\n📈 QUALITY IMPROVEMENT")
            print("-"*40)
            print(f"Average confidence:")
            print(f"  Before: {unfiltered_avg_conf:.3f}")
            print(f"  After:  {filtered_avg_conf:.3f} (+{filtered_avg_conf - unfiltered_avg_conf:.3f})")
            
            print(f"Average |offset|:")
            print(f"  Before: {unfiltered_avg_offset:.1f} frames")
            print(f"  After:  {filtered_avg_offset:.1f} frames ({filtered_avg_offset - unfiltered_avg_offset:+.1f})")
    
    # Filter criteria
    if 'quality_filters' in filtered_summary:
        filters = filtered_summary['quality_filters']
        print(f"\n🔧 FILTER CRITERIA")
        print("-"*40)
        print(f"Minimum confidence: ≥{filters['min_confidence']}")
        print(f"Maximum |offset|: ≤{filters['max_abs_offset']} frames")
        print(f"Filtering enabled: {filters['filter_enabled']}")
    
    # Accepted chunks details
    if 'accepted_chunks' in filtered_summary:
        print(f"\n✅ ACCEPTED CHUNKS ({len(filtered_summary['accepted_chunks'])})")
        print("-"*40)
        accepted_refs = set(filtered_summary['accepted_chunks'])
        
        for result in filtered_summary['results']:
            if result['reference'] in accepted_refs and result['status'] == 'success':
                print(f"  {result['reference']}: confidence={result['confidence']:.3f}, offset={result['offset']}")
    
    # Rejection reasons breakdown
    if 'rejected_chunks' in filtered_summary and filtered_summary['rejected_chunks']:
        print(f"\n❌ REJECTION BREAKDOWN ({len(filtered_summary['rejected_chunks'])} chunks)")
        print("-"*40)
        
        reason_counts = {}
        for rejected in filtered_summary['rejected_chunks']:
            if isinstance(rejected, dict) and 'reason' in rejected:
                for reason in rejected['reason']:
                    # Clean up reason for counting
                    if 'low_confidence' in reason:
                        key = 'Low confidence'
                    elif 'high_offset' in reason:
                        key = 'High offset'
                    elif 'no_faces' in reason:
                        key = 'No faces detected'
                    else:
                        key = reason
                    
                    reason_counts[key] = reason_counts.get(key, 0) + 1
        
        for reason, count in reason_counts.items():
            print(f"  {reason}: {count} chunks")
    
    # Recommendations
    if 'accepted_chunks' in filtered_summary:
        acceptance_rate = filtered_summary['acceptance_rate']
        
        print(f"\n💡 RECOMMENDATIONS")
        print("-"*40)
        
        if acceptance_rate >= 70:
            print("✅ Excellent filtering results! Most chunks meet quality standards.")
        elif acceptance_rate >= 50:
            print("⚠️  Moderate filtering results. Consider:")
            print("   - Relaxing filter criteria slightly")
            print("   - Checking source video quality")
        elif acceptance_rate >= 30:
            print("🔴 Low acceptance rate. Consider:")
            print("   - Significantly relaxing filter criteria")
            print("   - Using different videos with better sync")
        else:
            print("❌ Very low acceptance rate. Consider:")
            print("   - Disabling filtering temporarily")
            print("   - Checking video source quality")
            print("   - Using manual quality assessment")
        
        print(f"\n🎯 DATASET USAGE:")
        print(f"   - Use {len(filtered_summary['accepted_chunks'])} high-quality chunks for training")
        print(f"   - Total training data: ~{len(filtered_summary['accepted_chunks']) * 30} seconds")
        print(f"   - Audio files ready in: filtered_audio/")
        print(f"   - Video files ready in: filtered_chunks/")

def main():
    parser = argparse.ArgumentParser(description='Compare filtering results')
    parser.add_argument('unfiltered_summary', help='Path to unfiltered processing_summary.json')
    parser.add_argument('filtered_summary', help='Path to filtered processing_summary.json')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.unfiltered_summary):
        print(f"❌ Unfiltered summary not found: {args.unfiltered_summary}")
        return 1
    
    if not os.path.exists(args.filtered_summary):
        print(f"❌ Filtered summary not found: {args.filtered_summary}")
        return 1
    
    # Load summaries
    unfiltered_data = load_summary(args.unfiltered_summary)
    filtered_data = load_summary(args.filtered_summary)
    
    # Compare results
    compare_filtering_results(unfiltered_data, filtered_data)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
