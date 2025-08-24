"""
Audio-only CTC Model for Bengali Speech Recognition

Simple but effective architecture:
- 3-4 Conv1D blocks for acoustic feature extraction
- BiLSTM(2×256) for sequence modeling
- Linear projection to hidden dimension
- CTC head for character prediction
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional
import math


class Conv1DBlock(nn.Module):
    """Convolutional block with BatchNorm and ReLU"""
    
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.conv = nn.Conv1d(
            in_channels, out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding
        )
        self.bn = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, channels, time]
        Returns:
            x: [batch, channels, time]
        """
        x = self.conv(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.dropout(x)
        return x


class AudioCTCModel(nn.Module):
    """Audio-only CTC model for speech recognition"""
    
    def __init__(
        self,
        vocab_size: int,
        mel_bins: int = 80,
        conv_channels: list = [128, 256, 256, 512],
        conv_kernel_sizes: list = [3, 3, 3, 3],
        conv_strides: list = [1, 2, 1, 2],
        lstm_hidden: int = 256,
        lstm_layers: int = 2,
        hidden_dim: int = 512,
        dropout: float = 0.1
    ):
        """
        Initialize Audio CTC Model
        
        Args:
            vocab_size: Size of character vocabulary (including CTC blank)
            mel_bins: Number of mel filterbank features (input dimension)
            conv_channels: List of channel sizes for Conv1D blocks
            conv_kernel_sizes: Kernel sizes for each Conv1D block
            conv_strides: Stride values for each Conv1D block
            lstm_hidden: Hidden dimension for BiLSTM
            lstm_layers: Number of BiLSTM layers
            hidden_dim: Hidden dimension before CTC head
            dropout: Dropout rate
        """
        super().__init__()
        
        self.vocab_size = vocab_size
        self.mel_bins = mel_bins
        self.hidden_dim = hidden_dim
        
        # Conv1D feature extractor
        conv_layers = []
        in_channels = mel_bins
        
        for i, (out_channels, kernel_size, stride) in enumerate(
            zip(conv_channels, conv_kernel_sizes, conv_strides)
        ):
            padding = kernel_size // 2
            conv_layers.append(
                Conv1DBlock(
                    in_channels=in_channels,
                    out_channels=out_channels,
                    kernel_size=kernel_size,
                    stride=stride,
                    padding=padding,
                    dropout=dropout
                )
            )
            in_channels = out_channels
        
        self.conv_encoder = nn.Sequential(*conv_layers)
        
        # Calculate output length after convolutions
        self.conv_output_dim = conv_channels[-1]
        
        # BiLSTM for sequence modeling
        self.lstm = nn.LSTM(
            input_size=self.conv_output_dim,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            bidirectional=True,
            dropout=dropout if lstm_layers > 1 else 0,
            batch_first=True
        )
        
        # Linear projection to hidden dimension
        self.hidden_proj = nn.Linear(
            lstm_hidden * 2,  # bidirectional
            hidden_dim
        )
        
        # CTC head
        self.ctc_head = nn.Linear(hidden_dim, vocab_size)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize model weights"""
        for module in self.modules():
            if isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(module.weight, mode='fan_out', nonlinearity='relu')
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.BatchNorm1d):
                nn.init.constant_(module.weight, 1)
                nn.init.constant_(module.bias, 0)
            elif isinstance(module, nn.LSTM):
                for name, param in module.named_parameters():
                    if 'weight' in name:
                        nn.init.orthogonal_(param)
                    elif 'bias' in name:
                        nn.init.constant_(param, 0)
            elif isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight)
                if module.bias is not None:
                    nn.init.constant_(module.bias, 0)
    
    def forward(
        self,
        features: torch.Tensor,
        feature_lengths: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass
        
        Args:
            features: [batch, mel_bins, time] - mel spectrogram features
            feature_lengths: [batch] - actual lengths of features
            
        Returns:
            log_probs: [batch, time, vocab_size] - CTC log probabilities
            output_lengths: [batch] - actual output lengths
        """
        batch_size, mel_bins, max_time = features.shape
        
        # Conv1D feature extraction
        # Input: [batch, mel_bins, time]
        x = self.conv_encoder(features)
        # Output: [batch, conv_channels[-1], time']
        
        # Calculate output lengths after convolutions
        conv_time = x.shape[2]
        stride_product = 1
        for stride in [1, 2, 1, 2]:  # From conv_strides
            stride_product *= stride
        
        output_lengths = feature_lengths // stride_product
        output_lengths = torch.clamp(output_lengths, min=1, max=conv_time)
        
        # Transpose for LSTM: [batch, time, features]
        x = x.transpose(1, 2)
        
        # Pack sequences for efficient LSTM processing
        x_packed = nn.utils.rnn.pack_padded_sequence(
            x, output_lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        
        # BiLSTM
        lstm_out, _ = self.lstm(x_packed)
        
        # Unpack
        x, _ = nn.utils.rnn.pad_packed_sequence(lstm_out, batch_first=True)
        
        # Hidden projection
        x = self.hidden_proj(x)
        x = self.dropout(x)
        
        # CTC head
        logits = self.ctc_head(x)
        
        # Log softmax for CTC
        log_probs = F.log_softmax(logits, dim=-1)
        
        return log_probs, output_lengths
    
    def compute_ctc_loss(
        self,
        log_probs: torch.Tensor,
        targets: torch.Tensor,
        input_lengths: torch.Tensor,
        target_lengths: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute CTC loss
        
        Args:
            log_probs: [batch, time, vocab_size] - model outputs
            targets: [batch, max_target_len] - target sequences
            input_lengths: [batch] - actual input lengths
            target_lengths: [batch] - actual target lengths
            
        Returns:
            loss: CTC loss value
        """
        # CTC expects [time, batch, vocab_size]
        log_probs = log_probs.transpose(0, 1)
        
        # Flatten targets for CTC loss (remove padding)
        targets_flat = []
        target_lengths_list = target_lengths.tolist()
        
        for i, length in enumerate(target_lengths_list):
            targets_flat.extend(targets[i, :length].tolist())
        
        targets_flat = torch.tensor(targets_flat, dtype=torch.long, device=targets.device)
        
        # Compute CTC loss
        loss = F.ctc_loss(
            log_probs=log_probs,
            targets=targets_flat,
            input_lengths=input_lengths,
            target_lengths=target_lengths,
            blank=0,  # Assuming blank token is at index 0
            reduction='mean',
            zero_infinity=True
        )
        
        return loss
    
    def decode_greedy(
        self,
        log_probs: torch.Tensor,
        input_lengths: torch.Tensor
    ) -> list:
        """
        Greedy CTC decoding
        
        Args:
            log_probs: [batch, time, vocab_size]
            input_lengths: [batch] - actual sequence lengths
            
        Returns:
            decoded: List of decoded sequences (indices)
        """
        batch_size = log_probs.shape[0]
        decoded_sequences = []
        
        for i in range(batch_size):
            length = input_lengths[i].item()
            sequence = log_probs[i, :length]  # [time, vocab_size]
            
            # Get most likely tokens
            best_path = torch.argmax(sequence, dim=-1)  # [time]
            
            # Remove consecutive duplicates and blank tokens
            decoded = []
            prev_token = None
            
            for token in best_path:
                token = token.item()
                if token != 0 and token != prev_token:  # 0 is blank token
                    decoded.append(token)
                prev_token = token
            
            decoded_sequences.append(decoded)
        
        return decoded_sequences


def create_audio_ctc_model(
    vocab_size: int,
    mel_bins: int = 80,
    model_size: str = "small"
) -> AudioCTCModel:
    """
    Create Audio CTC model with predefined configurations
    
    Args:
        vocab_size: Size of character vocabulary
        mel_bins: Number of mel filterbank features
        model_size: Model size - "tiny", "small", "medium"
        
    Returns:
        AudioCTCModel instance
    """
    
    if model_size == "tiny":
        config = {
            "conv_channels": [64, 128, 128],
            "conv_kernel_sizes": [3, 3, 3],
            "conv_strides": [1, 2, 2],
            "lstm_hidden": 128,
            "lstm_layers": 1,
            "hidden_dim": 256,
            "dropout": 0.1
        }
    elif model_size == "small":
        config = {
            "conv_channels": [128, 256, 256, 512],
            "conv_kernel_sizes": [3, 3, 3, 3],
            "conv_strides": [1, 2, 1, 2],
            "lstm_hidden": 256,
            "lstm_layers": 2,
            "hidden_dim": 512,
            "dropout": 0.1
        }
    elif model_size == "medium":
        config = {
            "conv_channels": [128, 256, 512, 512, 1024],
            "conv_kernel_sizes": [3, 3, 3, 3, 3],
            "conv_strides": [1, 2, 1, 2, 1],
            "lstm_hidden": 512,
            "lstm_layers": 3,
            "hidden_dim": 1024,
            "dropout": 0.15
        }
    else:
        raise ValueError(f"Unknown model size: {model_size}")
    
    return AudioCTCModel(
        vocab_size=vocab_size,
        mel_bins=mel_bins,
        **config
    )


if __name__ == "__main__":
    # Test the model
    print("Testing AudioCTCModel...")
    
    vocab_size = 67  # Example vocab size (66 chars + blank)
    mel_bins = 80
    batch_size = 4
    max_time = 200
    
    # Create model
    model = create_audio_ctc_model(vocab_size, mel_bins, "small")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test forward pass
    features = torch.randn(batch_size, mel_bins, max_time)
    feature_lengths = torch.randint(50, max_time, (batch_size,))
    
    log_probs, output_lengths = model(features, feature_lengths)
    print(f"Output shape: {log_probs.shape}")
    print(f"Output lengths: {output_lengths}")
    
    # Test CTC loss
    targets = torch.randint(1, vocab_size, (batch_size, 20))  # Avoid blank token
    target_lengths = torch.randint(5, 20, (batch_size,))
    
    loss = model.compute_ctc_loss(log_probs, targets, output_lengths, target_lengths)
    print(f"CTC loss: {loss.item():.4f}")
    
    # Test decoding
    decoded = model.decode_greedy(log_probs, output_lengths)
    print(f"Decoded lengths: {[len(seq) for seq in decoded]}")
    
    print("Model test completed!")
