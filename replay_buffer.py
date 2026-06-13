"""
Experience replay buffer for offline DQN training.

Each transition stores:
  (state, action, reward, next_state, done, mask, next_mask)

where `mask` / `next_mask` are boolean arrays indicating which of the 9
action slots are legal in that state.
"""

from __future__ import annotations

import random
from collections import deque

import numpy as np


class ReplayBuffer:
    def __init__(self, capacity: int = 100_000):
        self._buf: deque[tuple] = deque(maxlen=capacity)

    def push(
        self,
        state:      np.ndarray,
        action:     int,
        reward:     float,
        next_state: np.ndarray,
        done:       bool,
        mask:       np.ndarray,
        next_mask:  np.ndarray,
    ) -> None:
        self._buf.append((
            np.array(state,      dtype=np.float32),
            int(action),
            float(reward),
            np.array(next_state, dtype=np.float32),
            bool(done),
            np.array(mask,       dtype=bool),
            np.array(next_mask,  dtype=bool),
        ))

    def sample(self, batch_size: int) -> tuple[np.ndarray, ...]:
        """
        Sample up to `batch_size` transitions at random.

        Returns a 7-tuple of stacked numpy arrays:
          (states, actions, rewards, next_states, dones, masks, next_masks)
        where dones is float32 (0.0 / 1.0) for easy Bellman computation.
        """
        batch = random.sample(self._buf, min(batch_size, len(self._buf)))
        states, actions, rewards, next_states, dones, masks, next_masks = zip(*batch)
        return (
            np.stack(states),
            np.array(actions,     dtype=np.int64),
            np.array(rewards,     dtype=np.float32),
            np.stack(next_states),
            np.array(dones,       dtype=np.float32),
            np.stack(masks),
            np.stack(next_masks),
        )

    def __len__(self) -> int:
        return len(self._buf)
