#!/usr/bin/env python3
"""
Results Analysis Script for SyncNet Processing
Analyzes and summarizes SyncNet results from processed video chunks
"""

import os
import json
import argparse
from pathlib import Path

def load_summary(summary_file):
    """Load processing summary JSON file"""
    with open(summary_file, 'r') as f:
        return json.load(f)

def analyze_sync_quality(results):
    """Analyze synchronization quality across chunks"""
    successful_chunks = [r for r in results if r['status'] == 'success']
    
    if not successful_chunks:
        return {"error": "No successful chunks found"}
    
    # Extract confidence scores and offsets
    confidences = [r['confidence'] for r in successful_chunks]
    offsets = [r['offset'] for r in successful_chunks]
    
    # Calculate statistics
    avg_confidence = sum(confidences) / len(confidences)
    max_confidence = max(confidences)
    min_confidence = min(confidences)
    
    avg_offset = sum(abs(o) for o in offsets) / len(offsets)
    
    # Categorize sync quality
    high_quality = [r for r in successful_chunks if r['confidence'] > 5.0]
    medium_quality = [r for r in successful_chunks if 2.0 <= r['confidence'] <= 5.0]
    low_quality = [r for r in successful_chunks if r['confidence'] < 2.0]
    
    return {
        "total_successful": len(successful_chunks),
        "average_confidence": avg_confidence,
        "max_confidence": max_confidence,
        "min_confidence": min_confidence,
        "average_abs_offset": avg_offset,
        "high_quality_chunks": len(high_quality),
        "medium_quality_chunks": len(medium_quality),
        "low_quality_chunks": len(low_quality),
        "best_chunk": max(successful_chunks, key=lambda x: x['confidence']),
        "worst_chunk": min(successful_chunks, key=lambda x: x['confidence'])
    }

def print_detailed_analysis(summary_data):
    """Print detailed analysis of results"""
    print("🎬 VIDEO PROCESSING ANALYSIS")
    print("="*60)
    
    # Basic stats
    print(f"📹 Input Video: {summary_data['input_video']}")
    print(f"⏱️  Total Chunks: {summary_data['total_chunks']}")
    print(f"✅ Successful Analysis: {summary_data['successful_analysis']}")
    print(f"❌ No Faces Detected: {summary_data['no_faces_chunks']}")
    print(f"⏰ Chunk Duration: {summary_data['chunk_duration']}s")
    print(f"🔄 Overlap: {summary_data['overlap']}s")
    
    # Quality filtering stats (if available)
    if 'accepted_chunks' in summary_data:
        print(f"\n🎯 QUALITY FILTERING")
        print("-"*40)
        print(f"✅ Accepted Chunks: {summary_data['accepted_chunks']}")
        print(f"❌ Rejected Chunks: {summary_data['rejected_chunks']}")
        print(f"📈 Acceptance Rate: {summary_data.get('acceptance_rate', 0):.1f}%")
        
        if 'quality_filters' in summary_data:
            filters = summary_data['quality_filters']
            print(f"🔍 Filter Settings:")
            print(f"   - Min Confidence: {filters.get('min_confidence', 'N/A')}")
            print(f"   - Max |Offset|: {filters.get('max_abs_offset', 'N/A')} frames")
            print(f"   - Filtering: {'Enabled' if filters.get('filter_enabled', False) else 'Disabled'}")
        
        # Show rejection reasons
        if 'rejected_chunks' in summary_data and summary_data['rejected_chunks']:
            print(f"\n🗑️  REJECTION REASONS:")
            rejection_counts = {}
            for rejected in summary_data['rejected_chunks']:
                if isinstance(rejected, dict) and 'reason' in rejected:
                    for reason in rejected['reason']:
                        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
            
            for reason, count in rejection_counts.items():
                print(f"   - {reason}: {count} chunks")
    
    # Sync quality analysis
    print(f"\n🎯 SYNCHRONIZATION ANALYSIS")
    print("-"*40)
    
    analysis = analyze_sync_quality(summary_data['results'])
    
    if 'error' in analysis:
        print(f"❌ {analysis['error']}")
        return
    
    print(f"📊 Average Confidence: {analysis['average_confidence']:.3f}")
    print(f"📈 Max Confidence: {analysis['max_confidence']:.3f}")
    print(f"📉 Min Confidence: {analysis['min_confidence']:.3f}")
    print(f"⚖️  Average Offset: {analysis['average_abs_offset']:.1f} frames")
    
    print(f"\n🏆 QUALITY BREAKDOWN")
    print("-"*40)
    print(f"🟢 High Quality (>5.0): {analysis['high_quality_chunks']} chunks")
    print(f"🟡 Medium Quality (2.0-5.0): {analysis['medium_quality_chunks']} chunks")
    print(f"🔴 Low Quality (<2.0): {analysis['low_quality_chunks']} chunks")
    
    # Best and worst chunks
    best = analysis['best_chunk']
    worst = analysis['worst_chunk']
    
    print(f"\n⭐ BEST CHUNK: {best['reference']}")
    print(f"   Confidence: {best['confidence']:.3f}, Offset: {best['offset']} frames")
    print(f"   Status: {best.get('quality_status', 'unknown')}")
    
    print(f"\n⚠️  WORST CHUNK: {worst['reference']}")
    print(f"   Confidence: {worst['confidence']:.3f}, Offset: {worst['offset']} frames")
    print(f"   Status: {worst.get('quality_status', 'unknown')}")

def list_output_files(base_dir):
    """List all generated output files"""
    print(f"\n📁 OUTPUT FILES")
    print("="*60)
    
    # Video chunks
    chunks_dir = os.path.join(base_dir, "chunks")
    if os.path.exists(chunks_dir):
        chunks = sorted(os.listdir(chunks_dir))
        print(f"📹 Video Chunks ({len(chunks)} files):")
        for chunk in chunks[:5]:  # Show first 5
            print(f"   - {chunk}")
        if len(chunks) > 5:
            print(f"   ... and {len(chunks) - 5} more")
    
    # Audio files
    audio_dir = os.path.join(base_dir, "audio")
    if os.path.exists(audio_dir):
        audio_files = sorted(os.listdir(audio_dir))
        print(f"\n🎵 Audio Files ({len(audio_files)} files):")
        for audio in audio_files[:5]:  # Show first 5
            print(f"   - {audio}")
        if len(audio_files) > 5:
            print(f"   ... and {len(audio_files) - 5} more")
    
    # SyncNet outputs
    syncnet_dir = os.path.join(base_dir, "syncnet_data")
    if os.path.exists(syncnet_dir):
        # Find offsets files
        import glob
        offsets_files = glob.glob(os.path.join(syncnet_dir, "**", "offsets.txt"), recursive=True)
        print(f"\n📊 SyncNet Analysis ({len(offsets_files)} results):")
        for offset_file in sorted(offsets_files)[:5]:
            rel_path = os.path.relpath(offset_file, syncnet_dir)
            print(f"   - {rel_path}")
        if len(offsets_files) > 5:
            print(f"   ... and {len(offsets_files) - 5} more")
        
        # Find visualization videos
        viz_videos = glob.glob(os.path.join(syncnet_dir, "**", "video_out.avi"), recursive=True)
        print(f"\n🎬 Visualization Videos ({len(viz_videos)} files):")
        for viz_video in sorted(viz_videos)[:5]:
            rel_path = os.path.relpath(viz_video, syncnet_dir)
            print(f"   - {rel_path}")
        if len(viz_videos) > 5:
            print(f"   ... and {len(viz_videos) - 5} more")

def recommend_next_steps(analysis_data):
    """Provide recommendations based on analysis"""
    print(f"\n💡 RECOMMENDATIONS")
    print("="*60)
    
    analysis = analyze_sync_quality(analysis_data['results'])
    
    if 'error' in analysis:
        print("❌ No successful analysis found")
        return
    
    # Quality recommendations
    if analysis['high_quality_chunks'] >= analysis['total_successful'] * 0.7:
        print("✅ Excellent sync quality! Most chunks show good lip-sync.")
    elif analysis['medium_quality_chunks'] >= analysis['total_successful'] * 0.5:
        print("⚠️  Moderate sync quality. Consider:")
        print("   - Check audio-video alignment in source")
        print("   - Verify face detection quality")
    else:
        print("🔴 Poor sync quality detected. Consider:")
        print("   - Check source video quality")
        print("   - Ensure clear face visibility")
        print("   - Verify audio quality")
    
    # Offset patterns
    successful_results = [r for r in analysis_data['results'] if r['status'] == 'success']
    offsets = [r['offset'] for r in successful_results]
    
    if all(abs(o) <= 2 for o in offsets):
        print("✅ Consistent sync across chunks (±2 frames)")
    elif max(abs(o) for o in offsets) > 10:
        print("⚠️  Large offset variations detected")
        print("   - May indicate source sync issues")
    
    # Usage suggestions
    print(f"\n🛠️  NEXT STEPS:")
    print("1. Review high-quality chunks for best results")
    print("2. Use visualization videos to verify face detection")
    print("3. Extract audio from best-sync chunks for training")
    print("4. Apply similar processing to other videos")

def main():
    parser = argparse.ArgumentParser(description='Analyze SyncNet processing results')
    parser.add_argument('summary_file', help='Path to processing_summary.json file')
    parser.add_argument('--detailed', action='store_true', help='Show detailed analysis')
    parser.add_argument('--list-files', action='store_true', help='List all output files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.summary_file):
        print(f"❌ Summary file not found: {args.summary_file}")
        return 1
    
    # Load summary
    summary_data = load_summary(args.summary_file)
    
    # Print analysis
    print_detailed_analysis(summary_data)
    
    if args.list_files:
        base_dir = os.path.dirname(args.summary_file)
        list_output_files(base_dir)
    
    if args.detailed:
        recommend_next_steps(summary_data)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
