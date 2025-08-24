"""
Training script for Audio-only CTC model

Supports mixed precision training, AdamW optimizer, gradient clipping,
and comprehensive logging.
"""

import os
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LinearLR, SequentialLR
import numpy as np
import logging
import argparse
from pathlib import Path
from tqdm import tqdm
import time
import json
from typing import Dict, Any

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent))
from data.dataset_audio_ctc import create_dataloader, AudioCTCDataset
from models.audio_ctc import create_audio_ctc_model
from utils.text_norm import BengaliTextNormalizer


class AudioCTCTrainer:
    """Trainer for Audio CTC model"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Setup logging
        self.setup_logging()
        
        # Create directories
        self.ckpt_dir = Path(config['ckpt_dir'])
        self.log_dir = Path(config['log_dir'])
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Save config
        with open(self.log_dir / 'config.yaml', 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Initialize components
        self.setup_data()
        self.setup_model()
        self.setup_optimizer()
        self.setup_training()
        
        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_val_loss = float('inf')
        
        # Metrics tracking
        self.train_losses = []
        self.val_losses = []
        self.learning_rates = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = Path(self.config['log_dir']) / 'training.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_data(self):
        """Setup data loaders"""
        self.logger.info("Setting up data loaders...")
        
        data_config = self.config['data']
        
        # Create data loaders
        self.train_loader = create_dataloader(
            manifest_csv=data_config['manifest'],
            charset_file=self.config['text']['charset'],
            split=data_config['split_train'],
            sample_rate=data_config['sample_rate'],
            mel_bins=data_config['mel_bins'],
            win_ms=data_config['win_ms'],
            hop_ms=data_config['hop_ms'],
            bucketing_sec=data_config['bucketing_sec'],
            num_workers=data_config['num_workers'],
            shuffle=True
        )
        
        self.val_loader = create_dataloader(
            manifest_csv=data_config['manifest'],
            charset_file=self.config['text']['charset'],
            split=data_config['split_val'],
            sample_rate=data_config['sample_rate'],
            mel_bins=data_config['mel_bins'],
            win_ms=data_config['win_ms'],
            hop_ms=data_config['hop_ms'],
            bucketing_sec=data_config['bucketing_sec'],
            num_workers=data_config['num_workers'],
            shuffle=False
        )
        
        # Get vocab size from dataset
        sample_dataset = AudioCTCDataset(
            data_config['manifest'],
            self.config['text']['charset'],
            split=data_config['split_train']
        )
        self.vocab_size = sample_dataset.vocab_size
        
        self.logger.info(f"Train samples: {len(self.train_loader.dataset)}")
        self.logger.info(f"Val samples: {len(self.val_loader.dataset)}")
        self.logger.info(f"Vocabulary size: {self.vocab_size}")
        
    def setup_model(self):
        """Setup model and move to device"""
        self.logger.info("Setting up model...")
        
        # Create model
        self.model = create_audio_ctc_model(
            vocab_size=self.vocab_size,
            mel_bins=self.config['data']['mel_bins'],
            model_size="small"  # Can be made configurable
        )
        
        # Move to device
        self.model = self.model.to(self.device)
        
        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        self.logger.info(f"Total parameters: {total_params:,}")
        self.logger.info(f"Trainable parameters: {trainable_params:,}")
        
    def setup_optimizer(self):
        """Setup optimizer and scheduler"""
        train_config = self.config['train']
        
        # Optimizer
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=train_config['lr'],
            weight_decay=0.01,
            betas=(0.9, 0.999)
        )
        
        # Scheduler with warmup
        warmup_steps = train_config['warmup_steps']
        total_steps = len(self.train_loader) * train_config['epochs']
        
        warmup_scheduler = LinearLR(
            self.optimizer,
            start_factor=0.1,
            end_factor=1.0,
            total_iters=warmup_steps
        )
        
        cosine_scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=total_steps - warmup_steps,
            eta_min=train_config['lr'] * 0.01
        )
        
        self.scheduler = SequentialLR(
            self.optimizer,
            schedulers=[warmup_scheduler, cosine_scheduler],
            milestones=[warmup_steps]
        )
        
        self.logger.info(f"Optimizer: AdamW (lr={train_config['lr']})")
        self.logger.info(f"Scheduler: LinearLR warmup + CosineAnnealingLR")
        self.logger.info(f"Warmup steps: {warmup_steps}")
        self.logger.info(f"Total steps: {total_steps}")
        
    def setup_training(self):
        """Setup training components"""
        train_config = self.config['train']
        
        # Mixed precision scaler
        self.scaler = torch.cuda.amp.GradScaler() if train_config['amp'] else None
        
        # Gradient clipping
        self.grad_clip = train_config['grad_clip']
        
        # Set random seed
        torch.manual_seed(train_config['seed'])
        np.random.seed(train_config['seed'])
        if torch.cuda.is_available():
            torch.cuda.manual_seed(train_config['seed'])
        
        self.logger.info(f"Mixed precision: {train_config['amp']}")
        self.logger.info(f"Gradient clipping: {self.grad_clip}")
        self.logger.info(f"Random seed: {train_config['seed']}")
        
    def train_epoch(self) -> float:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        progress_bar = tqdm(
            self.train_loader,
            desc=f"Epoch {self.current_epoch + 1}/{self.config['train']['epochs']}",
            leave=False
        )
        
        for batch in progress_bar:
            # Move to device
            audios = batch['audios'].to(self.device)
            audio_lens = batch['audio_lens'].to(self.device)
            targets = batch['targets'].to(self.device)
            target_lens = batch['target_lens'].to(self.device)
            
            # Zero gradients
            self.optimizer.zero_grad()
            
            # Forward pass with mixed precision
            if self.scaler is not None:
                with torch.cuda.amp.autocast():
                    log_probs, output_lengths = self.model(audios, audio_lens)
                    loss = self.model.compute_ctc_loss(
                        log_probs, targets, output_lengths, target_lens
                    )
                
                # Backward pass
                self.scaler.scale(loss).backward()
                
                # Gradient clipping
                if self.grad_clip > 0:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
                
                # Optimizer step
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                # Regular forward pass
                log_probs, output_lengths = self.model(audios, audio_lens)
                loss = self.model.compute_ctc_loss(
                    log_probs, targets, output_lengths, target_lens
                )
                
                # Backward pass
                loss.backward()
                
                # Gradient clipping
                if self.grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
                
                # Optimizer step
                self.optimizer.step()
            
            # Update scheduler
            self.scheduler.step()
            
            # Track metrics
            total_loss += loss.item()
            num_batches += 1
            self.global_step += 1
            
            # Update progress bar
            current_lr = self.optimizer.param_groups[0]['lr']
            progress_bar.set_postfix({
                'loss': f"{loss.item():.4f}",
                'lr': f"{current_lr:.2e}"
            })
            
            # Log periodically
            if self.global_step % 50 == 0:
                self.logger.info(
                    f"Step {self.global_step}: loss={loss.item():.4f}, lr={current_lr:.2e}"
                )
        
        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss
    
    def validate(self) -> float:
        """Validate the model"""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validating", leave=False):
                # Move to device
                audios = batch['audios'].to(self.device)
                audio_lens = batch['audio_lens'].to(self.device)
                targets = batch['targets'].to(self.device)
                target_lens = batch['target_lens'].to(self.device)
                
                # Forward pass
                with torch.cuda.amp.autocast() if self.scaler else torch.no_grad():
                    log_probs, output_lengths = self.model(audios, audio_lens)
                    loss = self.model.compute_ctc_loss(
                        log_probs, targets, output_lengths, target_lens
                    )
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / max(num_batches, 1)
        return avg_loss
    
    def save_checkpoint(self, epoch: int, is_best: bool = False):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'global_step': self.global_step,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_val_loss': self.best_val_loss,
            'config': self.config,
            'vocab_size': self.vocab_size
        }
        
        if self.scaler is not None:
            checkpoint['scaler_state_dict'] = self.scaler.state_dict()
        
        # Save regular checkpoint
        ckpt_path = self.ckpt_dir / f"checkpoint_epoch_{epoch:03d}.pt"
        torch.save(checkpoint, ckpt_path)
        
        # Save best checkpoint
        if is_best:
            best_path = self.ckpt_dir / "best_model.pt"
            torch.save(checkpoint, best_path)
            self.logger.info(f"Saved best model with val_loss={self.best_val_loss:.4f}")
        
        # Save latest checkpoint
        latest_path = self.ckpt_dir / "latest_model.pt"
        torch.save(checkpoint, latest_path)
        
    def train(self):
        """Main training loop"""
        self.logger.info("Starting training...")
        
        for epoch in range(self.config['train']['epochs']):
            self.current_epoch = epoch
            
            # Train
            train_loss = self.train_epoch()
            self.train_losses.append(train_loss)
            
            # Validate
            val_loss = self.validate()
            self.val_losses.append(val_loss)
            
            # Track learning rate
            current_lr = self.optimizer.param_groups[0]['lr']
            self.learning_rates.append(current_lr)
            
            # Check if best model
            is_best = val_loss < self.best_val_loss
            if is_best:
                self.best_val_loss = val_loss
            
            # Save checkpoint
            self.save_checkpoint(epoch, is_best)
            
            # Log epoch results
            self.logger.info(
                f"Epoch {epoch + 1}/{self.config['train']['epochs']}: "
                f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}, "
                f"lr={current_lr:.2e}, best_val_loss={self.best_val_loss:.4f}"
            )
            
            # Save training metrics
            metrics = {
                'epoch': epoch,
                'train_loss': train_loss,
                'val_loss': val_loss,
                'learning_rate': current_lr,
                'best_val_loss': self.best_val_loss
            }
            
            with open(self.log_dir / 'metrics.jsonl', 'a') as f:
                f.write(json.dumps(metrics) + '\n')
        
        self.logger.info("Training completed!")
        self.logger.info(f"Best validation loss: {self.best_val_loss:.4f}")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    parser = argparse.ArgumentParser(description="Train Audio CTC Model")
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to configuration YAML file'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Create trainer and train
    trainer = AudioCTCTrainer(config)
    trainer.train()


if __name__ == "__main__":
    main()
