import torch
import time
import numpy as np
from torch import nn
from torch.nn import functional as F
import sys
import os

class TimeDelayNetBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, dilation, padding="same", padding_mode="reflect"):
        super().__init__()
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size, dilation=dilation, padding=padding, padding_mode=padding_mode)
        self.activation = nn.ReLU()
    def forward(self, hidden_states: torch.Tensor):
        return self.activation(self.conv(hidden_states))

class AttentiveStatisticsPoolingOriginal(nn.Module):
    def __init__(self, channels, attention_channels=128):
        super().__init__()
        self.eps = 1e-12
        self.channels = channels
        self.tdnn = TimeDelayNetBlock(channels * 3, attention_channels, 1, 1)
        self.tanh = nn.Tanh()
        self.conv = nn.Conv1d(attention_channels, channels, 1, padding="same", padding_mode="reflect")
    def _length_to_mask(self, length, max_len=None, dtype=None, device=None):
        if max_len is None: max_len = length.max().long().item()
        mask = torch.arange(max_len, device=length.device, dtype=length.dtype).expand(len(length), max_len) < length.unsqueeze(1)
        mask = torch.as_tensor(mask, dtype=dtype, device=device)
        return mask
    def _compute_statistics(self, x, m, dim=2):
        mean = (m * x).sum(dim)
        std = torch.sqrt((m * (x - mean.unsqueeze(dim)).pow(2)).sum(dim).clamp(self.eps))
        return mean, std
    def forward(self, hidden_states):
        seq_length = hidden_states.shape[-1]
        lengths = torch.ones(hidden_states.shape[0], device=hidden_states.device)
        mask = self._length_to_mask(lengths * seq_length, max_len=seq_length, dtype=hidden_states.dtype, device=hidden_states.device).unsqueeze(1)
        total = mask.sum(dim=2, keepdim=True)
        mean, std = self._compute_statistics(hidden_states, mask / total)
        mean = mean.unsqueeze(2).expand(-1, -1, seq_length)
        std = std.unsqueeze(2).expand(-1, -1, seq_length)
        attention = torch.cat([hidden_states, mean, std], dim=1)
        attention = self.conv(self.tanh(self.tdnn(attention)))
        attention = attention.masked_fill(mask == 0, float("-inf"))
        attention = F.softmax(attention, dim=2)
        mean, std = self._compute_statistics(hidden_states, attention)
        pooled_stats = torch.cat((mean, std), dim=1).unsqueeze(2)
        return pooled_stats

class AttentiveStatisticsPoolingOptimized(nn.Module):
    def __init__(self, channels, attention_channels=128):
        super().__init__()
        self.eps = 1e-12
        self.channels = channels
        self.tdnn = TimeDelayNetBlock(channels * 3, attention_channels, 1, 1)
        self.tanh = nn.Tanh()
        self.conv = nn.Conv1d(attention_channels, channels, 1, padding="same", padding_mode="reflect")
    def _compute_statistics(self, x, m, dim=2):
        mean = (m * x).sum(dim)
        var = (m * x * x).sum(dim) - mean.pow(2)
        std = torch.sqrt(var.clamp(self.eps))
        return mean, std
    def forward(self, hidden_states):
        seq_length = hidden_states.shape[-1]
        mean = hidden_states.mean(dim=2)
        std = torch.sqrt(hidden_states.var(dim=2, unbiased=False).clamp(self.eps))
        tdnn_conv = self.tdnn.conv
        w = tdnn_conv.weight
        b = tdnn_conv.bias
        d = self.channels
        res = F.conv1d(hidden_states, w[:, :d, :], bias=b, padding="same")
        res_m = F.conv1d(mean.unsqueeze(2), w[:, d:2*d, :])
        res_s = F.conv1d(std.unsqueeze(2), w[:, 2*d:, :])
        attention = self.tdnn.activation(res + res_m + res_s)
        attention = self.conv(self.tanh(attention))
        attention = F.softmax(attention, dim=2)
        mean, std = self._compute_statistics(hidden_states, attention)
        pooled_stats = torch.cat((mean, std), dim=1).unsqueeze(2)
        return pooled_stats

def benchmark():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    B, C, L = 8, 512, 10000
    x = torch.randn(B, C, L).to(device)

    orig = AttentiveStatisticsPoolingOriginal(C).to(device)
    opt = AttentiveStatisticsPoolingOptimized(C).to(device)

    with torch.no_grad():
        opt.tdnn.conv.weight.copy_(orig.tdnn.conv.weight)
        opt.tdnn.conv.bias.copy_(orig.tdnn.conv.bias)
        opt.conv.weight.copy_(orig.conv.weight)
        opt.conv.bias.copy_(orig.conv.bias)

    for _ in range(10):
        _ = orig(x)
        _ = opt(x)

    torch.cuda.synchronize() if device == "cuda" else None
    start = time.time()
    for _ in range(100): y_orig = orig(x)
    torch.cuda.synchronize() if device == "cuda" else None
    t_orig = (time.time() - start) / 100

    start = time.time()
    for _ in range(100): y_opt = opt(x)
    torch.cuda.synchronize() if device == "cuda" else None
    t_opt = (time.time() - start) / 100

    print(f"Original: {t_orig*1000:.4f} ms")
    print(f"Optimized: {t_opt*1000:.4f} ms")
    print(f"Speedup: {t_orig/t_opt:.2f}x")
    diff = (y_orig - y_opt).abs().max().item()
    print(f"Max diff: {diff:.2e}")

if __name__ == "__main__":
    benchmark()
