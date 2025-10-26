#!/usr/bin/env python3
"""
Test Silence Detection Presets
==============================

Quick test to verify all presets are working correctly.
"""

from utils.split_by_silence import get_silence_preset

def test_presets():
    """Test all preset configurations."""
    
    presets = ['very_sensitive', 'sensitive', 'balanced', 'conservative', 'very_conservative']
    
    print("🧪 Testing Silence Detection Presets\n")
    print("=" * 80)
    
    for preset_name in presets:
        preset = get_silence_preset(preset_name)
        print(f"\n📊 Preset: {preset_name}")
        print(f"   Description: {preset['description']}")
        print(f"   Min Silence Length: {preset['min_silence_len']}ms")
        print(f"   Silence Offset: {preset['silence_offset']} dB")
        print(f"   Keep Silence: {preset['keep_silence']}ms")
        print(f"   Max Chunk Length: {preset['max_chunk_len']/1000:.1f}s")
    
    print("\n" + "=" * 80)
    print("✅ All presets loaded successfully!")
    
    # Test invalid preset
    print("\n🧪 Testing invalid preset handling...")
    invalid_preset = get_silence_preset('nonexistent')
    print(f"   Invalid preset returned: {invalid_preset == get_silence_preset('balanced')}")
    
    print("\n✅ Tests completed!\n")


if __name__ == "__main__":
    test_presets()
