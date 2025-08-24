"""
Audio CTC Dataset for Bengali Speech Recognition

Reads manifest.csv, loads audio (16k mono), applies text normalization,
builds character targets with bucketing by duration.
"""

import os
import csv
import torch
import torchaudio
import numpy as np
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from typing import List, Dict, Tuple, Optional
import logging

# Import text normalization
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.text_norm import BengaliTextNormalizer


logger = logging.getLogger(__name__)


class AudioCTCDataset(Dataset):
    """Dataset for audio-only CTC training"""
    
    def __init__(
        self,
        manifest_csv: str,
        charset_file: str,
        split: str = "train",
        sample_rate: int = 16000,
        mel_bins: int = 80,
        win_ms: int = 25,
        hop_ms: int = 10,
        text_normalizer: Optional[BengaliTextNormalizer] = None
    ):
        self.manifest_csv = manifest_csv
        self.split = split
        self.sample_rate = sample_rate
        self.mel_bins = mel_bins
        self.win_length = int(win_ms * sample_rate / 1000)  # 25ms window
        self.hop_length = int(hop_ms * sample_rate / 1000)   # 10ms hop
        
        # Load charset
        self.char_to_idx, self.idx_to_char = self._load_charset(charset_file)
        self.vocab_size = len(self.char_to_idx)
        
        # Initialize text normalizer
        if text_normalizer is None:
            text_normalizer = BengaliTextNormalizer()
        self.text_normalizer = text_normalizer
        
        # Load manifest data
        self.data = self._load_manifest()
        
        # Setup mel spectrogram transform
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=512,
            win_length=self.win_length,
            hop_length=self.hop_length,
            n_mels=mel_bins,
            power=2.0
        )
        
        logger.info(f"Loaded {len(self.data)} samples for split '{split}'")
        logger.info(f"Vocabulary size: {self.vocab_size}")
    
    def _load_charset(self, charset_file: str) -> Tuple[Dict[str, int], Dict[int, str]]:
        """Load character set mapping"""
        char_to_idx = {}
        idx_to_char = {}
        
        with open(charset_file, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                char = line.rstrip('\n\r')  # Only remove newlines, preserve spaces
                char_to_idx[char] = idx
                idx_to_char[idx] = char
        
        return char_to_idx, idx_to_char
    
    def _load_manifest(self) -> List[Dict]:
        """Load manifest data for specified split"""
        data = []
        
        with open(self.manifest_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['split'] == self.split and row['utt_id']:
                    # Choose best available transcript
                    google_txt = row.get('google_txt', '').strip()
                    whisper_txt = row.get('whisper_txt', '').strip()
                    
                    # Prefer longer non-empty transcript
                    if len(whisper_txt) > len(google_txt) and whisper_txt:
                        text = whisper_txt
                    elif google_txt:
                        text = google_txt
                    elif whisper_txt:
                        text = whisper_txt
                    else:
                        logger.warning(f"No transcript for {row['utt_id']}, skipping")
                        continue
                    
                    # Normalize text
                    normalized_text = self.text_normalizer.normalize(text)
                    
                    if not normalized_text:
                        logger.warning(f"Empty normalized text for {row['utt_id']}, skipping")
                        continue
                    
                    data.append({
                        'utt_id': row['utt_id'],
                        'audio_path': row['audio_path'],
                        'text': normalized_text,
                        'original_text': text
                    })
        
        return data
    
    def text_to_indices(self, text: str) -> List[int]:
        """Convert text to character indices"""
        indices = []
        for char in text:
            if char in self.char_to_idx:
                indices.append(self.char_to_idx[char])
            else:
                # Skip unknown characters or use a default token
                # Don't warn for common characters like space
                if char not in [' ', '\t', '\n']:
                    logger.warning(f"Unknown character '{char}' (U+{ord(char):04X})")
        return indices
    
    def indices_to_text(self, indices: List[int]) -> str:
        """Convert indices back to text"""
        chars = []
        for idx in indices:
            if idx in self.idx_to_char:
                char = self.idx_to_char[idx]
                if char != '<blank>':  # Skip CTC blank token
                    chars.append(char)
        return ''.join(chars)
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        """Get a single sample"""
        item = self.data[idx]
        
        # Load audio
        try:
            waveform, orig_sr = torchaudio.load(item['audio_path'])
            
            # Convert to mono if needed
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample if needed
            if orig_sr != self.sample_rate:
                resampler = torchaudio.transforms.Resample(orig_sr, self.sample_rate)
                waveform = resampler(waveform)
            
            # Squeeze to 1D
            waveform = waveform.squeeze(0)
            
        except Exception as e:
            logger.error(f"Error loading audio {item['audio_path']}: {e}")
            # Return empty waveform as fallback
            waveform = torch.zeros(self.sample_rate)  # 1 second of silence
        
        # Compute mel spectrogram
        mel_spec = self.mel_transform(waveform)
        mel_spec = torch.log(mel_spec + 1e-8)  # Log scale
        
        # Convert text to indices
        target_indices = self.text_to_indices(item['text'])
        
        return {
            'utt_id': item['utt_id'],
            'audio': mel_spec,  # [mel_bins, time_frames]
            'audio_len': mel_spec.shape[1],
            'target': torch.tensor(target_indices, dtype=torch.long),
            'target_len': len(target_indices),
            'text': item['text'],
            'original_text': item['original_text']
        }


def collate_fn(batch: List[Dict]) -> Dict:
    """Collate function for DataLoader with padding"""
    
    # Sort by audio length (for bucketing)
    batch = sorted(batch, key=lambda x: x['audio_len'], reverse=True)
    
    # Collect data
    utt_ids = [item['utt_id'] for item in batch]
    texts = [item['text'] for item in batch]
    original_texts = [item['original_text'] for item in batch]
    
    # Pad audio features
    max_audio_len = max(item['audio_len'] for item in batch)
    mel_bins = batch[0]['audio'].shape[0]
    
    audios = torch.zeros(len(batch), mel_bins, max_audio_len)
    audio_lens = torch.zeros(len(batch), dtype=torch.long)
    
    for i, item in enumerate(batch):
        audio = item['audio']
        audios[i, :, :audio.shape[1]] = audio
        audio_lens[i] = item['audio_len']
    
    # Pad targets
    max_target_len = max(item['target_len'] for item in batch)
    targets = torch.zeros(len(batch), max_target_len, dtype=torch.long)
    target_lens = torch.zeros(len(batch), dtype=torch.long)
    
    for i, item in enumerate(batch):
        target = item['target']
        targets[i, :len(target)] = target
        target_lens[i] = item['target_len']
    
    return {
        'utt_ids': utt_ids,
        'audios': audios,           # [batch, mel_bins, time]
        'audio_lens': audio_lens,   # [batch]
        'targets': targets,         # [batch, max_target_len]
        'target_lens': target_lens, # [batch]
        'texts': texts,
        'original_texts': original_texts
    }


class BucketingSampler:
    """Sampler that groups samples by similar duration for efficient batching"""
    
    def __init__(self, dataset: AudioCTCDataset, bucketing_sec: float = 40.0, shuffle: bool = True):
        self.dataset = dataset
        self.bucketing_sec = bucketing_sec
        self.shuffle = shuffle
        
        # Get durations and create buckets
        self.durations = []
        for i in range(len(dataset)):
            # Get audio length in seconds
            audio_len = dataset[i]['audio_len']
            duration = audio_len * dataset.hop_length / dataset.sample_rate
            self.durations.append((i, duration))
        
        # Sort by duration and create buckets
        self.durations.sort(key=lambda x: x[1])
        self.buckets = self._create_buckets()
        
        logger.info(f"Created {len(self.buckets)} buckets for {len(dataset)} samples")
        logger.info(f"Average bucket size: {len(dataset) / len(self.buckets):.1f}")
    
    def _create_buckets(self) -> List[List[int]]:
        """Create buckets based on duration"""
        buckets = []
        current_bucket = []
        current_duration = 0.0
        
        for idx, duration in self.durations:
            if current_duration + duration > self.bucketing_sec and current_bucket:
                # Start new bucket
                buckets.append(current_bucket)
                current_bucket = [idx]
                current_duration = duration
            else:
                # Add to current bucket
                current_bucket.append(idx)
                current_duration += duration
        
        # Add final bucket
        if current_bucket:
            buckets.append(current_bucket)
        
        return buckets
    
    def __iter__(self):
        if self.shuffle:
            # Shuffle buckets and shuffle within buckets
            np.random.shuffle(self.buckets)
            for bucket in self.buckets:
                np.random.shuffle(bucket)
        
        # Yield all indices
        for bucket in self.buckets:
            yield from bucket
    
    def __len__(self):
        return len(self.dataset)


def create_dataloader(
    manifest_csv: str,
    charset_file: str,
    split: str,
    sample_rate: int = 16000,
    mel_bins: int = 80,
    win_ms: int = 25,
    hop_ms: int = 10,
    bucketing_sec: float = 40.0,
    num_workers: int = 4,
    shuffle: bool = None
) -> DataLoader:
    """Create DataLoader with bucketing"""
    
    if shuffle is None:
        shuffle = (split == 'train')
    
    # Create dataset
    dataset = AudioCTCDataset(
        manifest_csv=manifest_csv,
        charset_file=charset_file,
        split=split,
        sample_rate=sample_rate,
        mel_bins=mel_bins,
        win_ms=win_ms,
        hop_ms=hop_ms
    )
    
    if len(dataset) == 0:
        raise ValueError(f"No data found for split '{split}'")
    
    # Create sampler for bucketing
    if bucketing_sec > 0:
        sampler = BucketingSampler(dataset, bucketing_sec, shuffle)
        # Use batch_size=1 since bucketing creates variable batch sizes
        batch_size = 1
        shuffle_dataloader = False
    else:
        sampler = None
        batch_size = 8  # Default batch size
        shuffle_dataloader = shuffle
    
    # Create DataLoader
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle_dataloader,
        sampler=sampler,
        collate_fn=collate_fn,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return dataloader


if __name__ == "__main__":
    # Test the dataset
    manifest_csv = "experiments/multimodal_compare/manifests/manifest.csv"
    charset_file = "experiments/multimodal_compare/manifests/charset.txt"
    
    print("Testing AudioCTCDataset...")
    
    # Test dataset
    dataset = AudioCTCDataset(manifest_csv, charset_file, split="train")
    print(f"Dataset size: {len(dataset)}")
    print(f"Vocab size: {dataset.vocab_size}")
    
    # Test single sample
    sample = dataset[0]
    print(f"Sample keys: {sample.keys()}")
    print(f"Audio shape: {sample['audio'].shape}")
    print(f"Target shape: {sample['target'].shape}")
    print(f"Text: {sample['text']}")
    
    # Test DataLoader
    print("\nTesting DataLoader...")
    dataloader = create_dataloader(manifest_csv, charset_file, "train", bucketing_sec=20.0)
    
    for i, batch in enumerate(dataloader):
        print(f"Batch {i}: audio={batch['audios'].shape}, targets={batch['targets'].shape}")
        if i >= 2:  # Only test a few batches
            break
    
    print("Dataset test completed!")
