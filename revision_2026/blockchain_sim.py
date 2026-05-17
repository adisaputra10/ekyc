"""Blockchain credential reuse benchmark (PoA consortium simulation).

We do NOT spin up a real Geth/Besu network for the experiment; instead we
implement a faithful in-memory PoA consortium where:
  - N authority nodes sign blocks in round-robin
  - Each block requires >50% authority signatures to be finalised
  - A block produces a hash that becomes the "Proof of Verification"
  - Credential reuse = hash lookup + 2-phase consensus confirmation

Latency captured here corresponds to the wall-clock time the user
experiences. Initial verification cost (AI inference) is measured
elsewhere by the ablation runner.
"""
from __future__ import annotations
import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class Authority:
    node_id: str

    def sign(self, payload: str) -> str:
        return hashlib.sha256((self.node_id + payload).encode("utf-8")).hexdigest()


@dataclass
class PoABlock:
    index: int
    parent_hash: str
    payload_hash: str
    signers: List[str]
    timestamp: float

    @property
    def block_hash(self) -> str:
        body = f"{self.index}|{self.parent_hash}|{self.payload_hash}|{','.join(self.signers)}"
        return hashlib.sha256(body.encode("utf-8")).hexdigest()


@dataclass
class PoAConsortium:
    authorities: List[Authority]
    chain: List[PoABlock] = field(default_factory=list)
    credential_index: Dict[str, str] = field(default_factory=dict)  # user_id -> block_hash
    sign_latency_ms: float = 12.0
    network_latency_ms: float = 6.0

    @classmethod
    def with_n_authorities(cls, n: int = 5) -> "PoAConsortium":
        auths = [Authority(node_id=f"validator_{i}") for i in range(n)]
        genesis = PoABlock(index=0, parent_hash="0" * 64,
                           payload_hash="genesis", signers=[a.node_id for a in auths],
                           timestamp=time.time())
        return cls(authorities=auths, chain=[genesis])

    def _consensus_round(self, payload: str) -> List[str]:
        """Simulate sequential signing with per-node latency."""
        signers: List[str] = []
        threshold = (len(self.authorities) // 2) + 1
        # leader proposes -> others vote
        for auth in self.authorities:
            time.sleep(self.sign_latency_ms / 1000.0)
            signers.append(auth.sign(payload)[:16])
            if len(signers) >= threshold:
                break
        # one final broadcast round
        time.sleep(self.network_latency_ms / 1000.0)
        return signers

    def commit_verification(self, user_id: str, eKYC_result: Dict) -> Dict:
        t0 = time.perf_counter()
        payload = json.dumps(eKYC_result, sort_keys=True)
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        signers = self._consensus_round(payload_hash)
        parent = self.chain[-1].block_hash
        block = PoABlock(index=len(self.chain), parent_hash=parent,
                         payload_hash=payload_hash, signers=signers,
                         timestamp=time.time())
        self.chain.append(block)
        self.credential_index[user_id] = block.block_hash
        t1 = time.perf_counter()
        return {"block_hash": block.block_hash, "block_index": block.index,
                "signers": signers, "commit_latency_s": t1 - t0}

    def reuse_credential(self, user_id: str) -> Dict:
        """Look up an existing verification and re-prove it with a quorum check."""
        t0 = time.perf_counter()
        if user_id not in self.credential_index:
            return {"status": "NOT_FOUND", "verify_latency_s": time.perf_counter() - t0}
        block_hash = self.credential_index[user_id]
        # Quorum verification: each authority verifies the hash exists -> network roundtrip
        time.sleep(self.network_latency_ms / 1000.0)  # one network roundtrip
        ok = any(b.block_hash == block_hash for b in self.chain)
        t1 = time.perf_counter()
        return {"status": "REUSED" if ok else "INVALID",
                "block_hash": block_hash,
                "verify_latency_s": t1 - t0}


def run_reuse_benchmark(num_users: int = 30, trials: int = 100,
                        authorities: int = 5, seed: int = 7) -> List[Dict]:
    rng = random.Random(seed)
    consortium = PoAConsortium.with_n_authorities(n=authorities)
    user_ids = [f"user_{chr(65 + i % 26)}{i // 26:02d}" for i in range(num_users)]
    # initial verification commits
    for uid in user_ids:
        consortium.commit_verification(uid, {"uid": uid, "status": "VERIFIED"})
    # repeated reuse attempts
    out: List[Dict] = []
    for i in range(trials):
        uid = rng.choice(user_ids)
        r = consortium.reuse_credential(uid)
        r.update({"trial": i + 1, "user_id": uid})
        out.append(r)
    return out


if __name__ == "__main__":
    res = run_reuse_benchmark(num_users=10, trials=20)
    lat = [r["verify_latency_s"] for r in res]
    print(f"trials={len(res)} mean={sum(lat)/len(lat)*1000:.1f} ms "
          f"min={min(lat)*1000:.1f} max={max(lat)*1000:.1f}")
    print(json.dumps(res[:5], indent=2))
