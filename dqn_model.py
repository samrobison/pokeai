"""
Dueling Double DQN for Pokemon battles.

Architecture:
  Input  (STATE_DIM = 671)
    → Linear(671→512) + LayerNorm + ReLU + Dropout(0.1)
    → Linear(512→256) + ReLU
    → Linear(256→128) + ReLU
    → splits into two heads:
         Value stream:     Linear(128→64) + ReLU → Linear(64→1)
         Advantage stream: Linear(128→64) + ReLU → Linear(64→ACTION_DIM)
  Q(s,a) = V(s) + [A(s,a) − mean_a A(s,a)]

Dueling nets have lower variance on less-visited actions.
Double DQN (separate online/target networks) is handled in the training loop.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch
import torch.nn as nn

from state_encoder import STATE_DIM, ACTION_DIM


class DuelingDQN(nn.Module):
    """Dueling Deep Q-Network for Pokemon battle decisions."""

    def __init__(
        self,
        state_dim: int = STATE_DIM,
        action_dim: int = ACTION_DIM,
        hidden: list[int] | None = None,
    ):
        super().__init__()
        if hidden is None:
            hidden = [512, 256, 128]

        # Shared trunk
        layers: list[nn.Module] = []
        in_dim = state_dim
        for i, out_dim in enumerate(hidden):
            layers.append(nn.Linear(in_dim, out_dim))
            if i == 0:
                layers.append(nn.LayerNorm(out_dim))
            layers.append(nn.ReLU())
            if i == 0:
                layers.append(nn.Dropout(0.1))
            in_dim = out_dim
        self.trunk = nn.Sequential(*layers)

        # Dueling heads
        branch_in = hidden[-1]
        self.value_head = nn.Sequential(
            nn.Linear(branch_in, 64), nn.ReLU(),
            nn.Linear(64, 1),
        )
        self.adv_head = nn.Sequential(
            nn.Linear(branch_in, 64), nn.ReLU(),
            nn.Linear(64, action_dim),
        )

        # Store dims for checkpoint compatibility
        self.state_dim  = state_dim
        self.action_dim = action_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, state_dim) float tensor
        Returns:
            Q-values of shape (B, action_dim)
        """
        h = self.trunk(x)
        v = self.value_head(h)                          # (B, 1)
        a = self.adv_head(h)                            # (B, A)
        return v + a - a.mean(dim=1, keepdim=True)      # dueling combination

    # ── Inference helpers ─────────────────────────────────────────────────────

    @torch.no_grad()
    def q_values(
        self,
        state: np.ndarray,
        mask: Optional[np.ndarray] = None,
        device: str = "cpu",
    ) -> np.ndarray:
        """
        Compute Q-values for a single state.

        Args:
            state: float32 array of shape (STATE_DIM,)
            mask:  bool array of shape (ACTION_DIM,); invalid actions → −∞
            device: torch device string

        Returns:
            float32 array of shape (ACTION_DIM,)
        """
        self.eval()
        t = torch.FloatTensor(state).unsqueeze(0).to(device)
        q = self.forward(t).squeeze(0).cpu().numpy()
        if mask is not None:
            q[~mask] = -1e9
        return q

    def best_action(
        self,
        state: np.ndarray,
        mask: Optional[np.ndarray] = None,
        device: str = "cpu",
    ) -> int:
        """Return the greedy action index (0–8)."""
        return int(np.argmax(self.q_values(state, mask, device)))

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        torch.save(
            {
                "model_state": self.state_dict(),
                "state_dim":   self.state_dim,
                "action_dim":  self.action_dim,
            },
            path,
        )
        print(f"Model saved → {path}")

    @classmethod
    def load(cls, path: str, device: str = "cpu") -> DuelingDQN:
        checkpoint = torch.load(path, map_location=device)
        model = cls(
            state_dim  = checkpoint.get("state_dim",  STATE_DIM),
            action_dim = checkpoint.get("action_dim", ACTION_DIM),
        ).to(device)
        model.load_state_dict(checkpoint["model_state"])
        model.eval()
        return model
