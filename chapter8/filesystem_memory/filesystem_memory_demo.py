#!/usr/bin/env python3
"""
Lesson 3: Filesystem as Context Demo

This demo stores complete observations outside a model prompt in local files.
Demonstrates recoverable compression, state externalization, and persistent memory.
"""

import json
import hashlib
import tempfile
import shutil
from uuid import uuid4
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime


@dataclass 
class MemoryStats:
    """Statistics for filesystem memory usage"""
    total_files: int = 0
    total_size_bytes: int = 0
    compressed_observations: int = 0
    externalized_states: int = 0
    compression_ratio: float = 0.0
    
    
class FilesystemMemoryEngine:
    """
    Filesystem as context implementation demonstrating:
    - External memory bounded by available disk space
    - Recoverable information compression
    - State externalization and persistence
    - Cross-session memory continuity
    """
    
    def __init__(self, workspace_dir: Optional[str] = None, auto_cleanup: bool = True):
        self.workspace_dir = Path(workspace_dir or tempfile.mkdtemp(prefix="agent_memory_"))
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.auto_cleanup = auto_cleanup
        
        # Memory organization
        self.observations_dir = self.workspace_dir / "observations"
        self.states_dir = self.workspace_dir / "states"
        self.compressed_dir = self.workspace_dir / "compressed"
        self.index_file = self.workspace_dir / "memory_index.json"
        
        # Create subdirectories
        for dir_path in [self.observations_dir, self.states_dir, self.compressed_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.memory_index = self._load_or_create_index()
        self.compression_map = {}
        
    def _load_or_create_index(self) -> Dict[str, Any]:
        """Load existing memory index or create new one"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {
            "created": datetime.now().isoformat(),
            "observations": {},
            "states": {},
            "compression_stats": {}
        }
    
    def _save_index(self):
        """Save memory index to filesystem"""
        with open(self.index_file, 'w') as f:
            json.dump(self.memory_index, f, indent=2)
    
    def externalize_large_observation(self, observation: Dict[str, Any], 
                                    preserve_keys: List[str] = None) -> str:
        """
        Externalize large observation to filesystem with recoverable compression
        
        Args:
            observation: Large observation to compress
            preserve_keys: Keys to preserve in compressed reference
            
        Returns:
            Compressed reference string
        """
        preserve_keys = preserve_keys or []
        
        # Generate unique ID for this observation
        obs_content = json.dumps(observation, sort_keys=True)
        obs_id = hashlib.md5(obs_content.encode()).hexdigest()[:12]
        
        # Store full observation
        obs_file = self.observations_dir / f"obs_{obs_id}.json"
        with open(obs_file, 'w') as f:
            json.dump(observation, f, indent=2)
        
        # Create compressed reference
        compressed_obs = {
            "type": "externalized_observation",
            "id": obs_id,
            "recovery_path": str(obs_file.relative_to(self.workspace_dir)),
            "original_size": len(obs_content),
            "compressed_size": 0,  # Will be calculated
            "timestamp": datetime.now().isoformat(),
            "preserve_keys": preserve_keys
        }
        
        # Preserve specified keys in the compressed reference
        for key in preserve_keys:
            if key in observation:
                compressed_obs[f"preserved_{key}"] = observation[key]
        
        # Store compressed reference
        compressed_ref = json.dumps(compressed_obs)
        while compressed_obs["compressed_size"] != len(compressed_ref.encode("utf-8")):
            compressed_obs["compressed_size"] = len(compressed_ref.encode("utf-8"))
            compressed_ref = json.dumps(compressed_obs)
        
        # Update index
        self.memory_index["observations"][obs_id] = {
            "file_path": str(obs_file),
            "original_size": len(obs_content),
            "compressed_size": len(compressed_ref),
            "compression_ratio": len(compressed_ref) / len(obs_content),
            "preserved_keys": preserve_keys,
            "created": datetime.now().isoformat()
        }
        
        self.compression_map[obs_id] = str(obs_file)
        self._save_index()
        
        print(f"🗂️  Externalized observation {obs_id}")
        print(f"   Original size: {len(obs_content):,} bytes")
        print(f"   Compressed size: {len(compressed_ref):,} bytes") 
        print(f"   Compression ratio: {(len(compressed_ref) / len(obs_content)):.2%}")
        print(f"   Preserved keys: {preserve_keys}")
        
        return compressed_ref
    
    def restore_observation(self, obs_id: str) -> Optional[Dict[str, Any]]:
        """Restore full observation from filesystem"""
        if obs_id in self.compression_map:
            obs_file = Path(self.compression_map[obs_id])
        elif obs_id in self.memory_index["observations"]:
            obs_file = Path(self.memory_index["observations"][obs_id]["file_path"])
        else:
            print(f"❌ Observation {obs_id} not found in memory")
            return None
            
        if obs_file.exists():
            with open(obs_file, 'r') as f:
                restored = json.load(f)
                print(f"✅ Restored observation {obs_id} ({len(json.dumps(restored)):,} bytes)")
                return restored
        else:
            print(f"❌ Observation file {obs_file} not found")
            return None
    
    def externalize_agent_state(self, state: Dict[str, Any], state_name: str = "default") -> str:
        """Externalize complete agent state to filesystem"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        state_id = f"{state_name}_{timestamp}_{uuid4().hex[:8]}"
        
        # Add metadata to state
        state_with_metadata = {
            "state_id": state_id,
            "state_name": state_name,
            "timestamp": datetime.now().isoformat(),
            "agent_state": state
        }
        
        # Save to filesystem
        state_file = self.states_dir / f"state_{state_id}.json"
        with open(state_file, 'w') as f:
            json.dump(state_with_metadata, f, indent=2)
        
        # Update index
        self.memory_index["states"][state_id] = {
            "file_path": str(state_file),
            "state_name": state_name,
            "size_bytes": state_file.stat().st_size,
            "created": datetime.now().isoformat()
        }
        self._save_index()
        
        print(f"💾 Externalized agent state '{state_name}' as {state_id}")
        print(f"   File: {state_file.name}")
        print(f"   Size: {state_file.stat().st_size:,} bytes")
        
        return state_id
    
    def restore_agent_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Restore agent state from filesystem"""
        if state_id not in self.memory_index["states"]:
            print(f"❌ State {state_id} not found")
            return None
        
        state_file = Path(self.memory_index["states"][state_id]["file_path"])
        if state_file.exists():
            with open(state_file, 'r') as f:
                state_data = json.load(f)
                print(f"✅ Restored agent state {state_id}")
                return state_data["agent_state"]
        else:
            print(f"❌ State file {state_file} not found")
            return None
    
    def get_latest_state(self, state_name: str = "default") -> Optional[Dict[str, Any]]:
        """Get the most recent state with given name"""
        matching_states = [
            (state_id, info) for state_id, info in self.memory_index["states"].items()
            if info["state_name"] == state_name
        ]
        
        if not matching_states:
            return None
        
        # Sort by creation time and get latest
        latest_state_id = sorted(matching_states, key=lambda x: x[1]["created"])[-1][0]
        return self.restore_agent_state(latest_state_id)
    
    def create_memory_snapshot(self, snapshot_name: str) -> str:
        """Create a snapshot of entire memory state"""
        snapshot = {
            "snapshot_name": snapshot_name,
            "created": datetime.now().isoformat(),
            "memory_index": self.memory_index.copy(),
            "workspace_structure": self._analyze_workspace_structure(),
            "statistics": asdict(self.get_memory_statistics())
        }
        
        snapshot_file = self.workspace_dir / f"snapshot_{snapshot_name}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"📸 Created memory snapshot: {snapshot_name}")
        return str(snapshot_file)
    
    def _analyze_workspace_structure(self) -> Dict[str, Any]:
        """Analyze current workspace directory structure"""
        structure = {
            "directories": {},
            "total_files": 0,
            "total_size": 0
        }
        
        for item in self.workspace_dir.rglob('*'):
            if item.is_file():
                structure["total_files"] += 1
                structure["total_size"] += item.stat().st_size
                
                # Categorize by directory
                rel_dir = str(item.parent.relative_to(self.workspace_dir))
                if rel_dir not in structure["directories"]:
                    structure["directories"][rel_dir] = {"files": 0, "size": 0}
                structure["directories"][rel_dir]["files"] += 1
                structure["directories"][rel_dir]["size"] += item.stat().st_size
        
        return structure
    
    def get_memory_statistics(self) -> MemoryStats:
        """Get comprehensive memory usage statistics"""
        total_files = 0
        total_size = 0
        
        # Count all files in workspace
        for file_path in self.workspace_dir.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        # Calculate compression statistics
        total_original_size = sum(
            info["original_size"] for info in self.memory_index["observations"].values()
        )
        total_compressed_size = sum(
            info["compressed_size"] for info in self.memory_index["observations"].values()  
        )
        
        compression_ratio = (
            total_compressed_size / total_original_size 
            if total_original_size > 0 else 0.0
        )
        
        return MemoryStats(
            total_files=total_files,
            total_size_bytes=total_size,
            compressed_observations=len(self.memory_index["observations"]),
            externalized_states=len(self.memory_index["states"]),
            compression_ratio=compression_ratio
        )
    
    def cleanup(self):
        """Clean up temporary filesystem memory"""
        if self.auto_cleanup and self.workspace_dir.exists():
            shutil.rmtree(self.workspace_dir)
            print(f"🧹 Cleaned up memory workspace: {self.workspace_dir}")


def demonstrate_large_observation_handling():
    """Demonstrate handling of large observations"""
    print("🗂️  === Large Observation Handling Demo ===\n")
    
    memory = FilesystemMemoryEngine()
    
    # Create increasingly large observations
    observations = [
        {
            "type": "web_page",
            "url": "https://example.com/small-page",
            "title": "Small Web Page",
            "content": "This is a small web page content. " * 10,
            "metadata": {"size": "small", "words": 100}
        },
        {
            "type": "pdf_document", 
            "url": "https://example.com/medium-doc.pdf",
            "title": "Medium Research Paper",
            "content": "This is a medium-sized research document. " * 200,
            "metadata": {"size": "medium", "pages": 50, "citations": 150}
        },
        {
            "type": "database_dump",
            "source": "user_analytics_db",
            "title": "Large Database Export",
            "content": "Row data: " + ", ".join([f"user_{i}:data_{i}" for i in range(1000)]),
            "metadata": {"size": "large", "rows": 1000, "tables": 5}
        }
    ]
    
    for i, obs in enumerate(observations, 1):
        print(f"--- Observation {i}: {obs['title']} ---")
        preserve_keys = ["url", "title", "metadata"] if "url" in obs else ["source", "title", "metadata"]
        
        compressed_ref = memory.externalize_large_observation(obs, preserve_keys)
        
        # Parse the compressed reference to show what's preserved
        compressed_data = json.loads(compressed_ref)
        print(f"   Preserved data accessible without restoration:")
        for key in preserve_keys:
            if f"preserved_{key}" in compressed_data:
                print(f"     {key}: {compressed_data[f'preserved_{key}']}")
        print()
    
    # Demonstrate restoration
    print("--- Testing Observation Restoration ---")
    for obs_id in memory.compression_map.keys():
        restored = memory.restore_observation(obs_id)
        if restored:
            print(f"   Successfully restored {obs_id}: {restored['title']}")
    
    return memory


def demonstrate_state_persistence():
    """Demonstrate agent state externalization and persistence"""
    print("\n💾 === Agent State Persistence Demo ===\n")
    
    memory = FilesystemMemoryEngine()
    
    # Simulate agent states during different phases
    states = [
        {
            "name": "initialization",
            "state": {
                "conversation_history": [],
                "tools_loaded": ["file_read", "web_search"],
                "current_task": "startup",
                "memory_usage": {"ram": "100MB", "disk": "0MB"},
                "performance_metrics": {"requests": 0, "cache_hits": 0}
            }
        },
        {
            "name": "active_conversation", 
            "state": {
                "conversation_history": [
                    {"user": "Hello", "assistant": "Hi there!"},
                    {"user": "Help with Python", "assistant": "Sure, what do you need?"}
                ],
                "tools_loaded": ["file_read", "web_search", "code_analyze"],
                "current_task": "coding_assistance",
                "memory_usage": {"ram": "250MB", "disk": "50MB"},
                "performance_metrics": {"requests": 5, "cache_hits": 2}
            }
        },
        {
            "name": "complex_project",
            "state": {
                "conversation_history": [{"summarized": "10 previous exchanges"}],
                "tools_loaded": ["file_read", "file_write", "web_search", "code_analyze", "code_test"],
                "current_task": "web_app_development", 
                "project_context": {
                    "files_modified": ["app.py", "models.py", "requirements.txt"],
                    "tests_run": 15,
                    "build_status": "passing"
                },
                "memory_usage": {"ram": "500MB", "disk": "200MB"},
                "performance_metrics": {"requests": 50, "cache_hits": 30}
            }
        }
    ]
    
    # Externalize each state
    state_ids = []
    for state_info in states:
        state_id = memory.externalize_agent_state(state_info["state"], state_info["name"])
        state_ids.append((state_id, state_info["name"]))
        
    print()
    
    # Demonstrate state restoration
    print("--- Testing State Restoration ---")
    for state_id, name in state_ids:
        restored = memory.restore_agent_state(state_id)
        if restored:
            print(f"✅ Restored '{name}' state")
            print(f"   Current task: {restored.get('current_task', 'unknown')}")
            print(f"   Memory usage: {restored.get('memory_usage', {})}")
            print(f"   Performance: {restored.get('performance_metrics', {})}")
        print()
    
    # Test getting latest state
    print("--- Testing Latest State Retrieval ---")
    latest = memory.get_latest_state("active_conversation")
    if latest:
        print("✅ Retrieved latest 'active_conversation' state")
        print(f"   Conversation length: {len(latest.get('conversation_history', []))}")
    
    return memory


def demonstrate_cross_session_persistence(workspace_dir=None, phase="both"):
    """Save and resume teaching state, optionally in separate processes."""
    workspace = Path(workspace_dir or tempfile.mkdtemp(prefix="persistent_memory_"))
    if phase == "resume" and not (workspace / "memory_index.json").is_file():
        raise ValueError("请先在同一 --workspace 运行 --phase save。")

    web_data = {
        "type": "research_results",
        "query": "AI agent architecture patterns",
        "results": ["Result " + str(i) for i in range(100)],
        "metadata": {"search_engine": "academic", "relevance": "high"}
    }
    if phase != "resume":
        print("--- Session 1: Creating Memory ---")
        session1_memory = FilesystemMemoryEngine(workspace, auto_cleanup=False)
        reference = session1_memory.externalize_large_observation(
            web_data, ["type", "query", "metadata"]
        )
        print(f"压缩引用：{reference}")
        session1_memory.externalize_agent_state({
            "research_progress": "completed_search",
            "next_steps": ["analyze_results", "write_summary"],
            "workspace_files": ["notes.md", "references.json"]
        }, "research_session")
        session1_memory.create_memory_snapshot("session1_end")
        print(f"Session 1 complete. Memory saved to: {workspace}")
        if phase == "save":
            return session1_memory

    print("--- Session 2: Restoring Memory ---")
    session2_memory = FilesystemMemoryEngine(workspace, auto_cleanup=False)
    latest_state = session2_memory.get_latest_state("research_session")
    if latest_state is None:
        raise ValueError("未找到 research_session 状态，请检查 --workspace。")
    observation_id = hashlib.md5(json.dumps(web_data, sort_keys=True).encode()).hexdigest()[:12]
    restored_observation = session2_memory.restore_observation(observation_id)
    if restored_observation != web_data:
        raise RuntimeError("恢复的观察内容与保存的教学数据不一致。")
    print(f"完整观察恢复一致，包含 {len(restored_observation['results'])} 条结果。")
    print(f"Resumed research at: {latest_state['research_progress']}")
    print(f"Next steps: {latest_state['next_steps']}")

    updated_state = latest_state.copy()
    updated_state["research_progress"] = "analyzing_results"
    updated_state["next_steps"] = ["write_summary", "create_presentation"]
    updated_state["analysis_notes"] = "Found 3 key patterns in agent architectures"
    session2_memory.externalize_agent_state(updated_state, "research_session")
    print(f"State versions retained: {len(session2_memory.memory_index['states'])}")
    print(f"Workspace retained for inspection: {workspace}")
    return session2_memory


def run_comprehensive_demo():
    """Run comprehensive filesystem memory demonstration"""
    print("🗂️  Filesystem as Context & Externalized Memory Demo\n")
    
    # Demo 1: Large observation handling
    memory1 = demonstrate_large_observation_handling()
    
    # Demo 2: State persistence
    memory2 = demonstrate_state_persistence()
    
    # Demo 3: Cross-session persistence
    memory3 = demonstrate_cross_session_persistence()
    
    print("\n" + "="*60)
    print("📊 MEMORY STATISTICS")
    print("="*60)
    
    # Show statistics from main demo
    stats = memory1.get_memory_statistics()
    print(f"Total Files: {stats.total_files}")
    print(f"Total Size: {stats.total_size_bytes:,} bytes")
    print(f"Compressed Observations: {stats.compressed_observations}")
    print(f"Externalized States: {stats.externalized_states}")
    print(f"Average Compression Ratio: {stats.compression_ratio:.2%}")
    
    print("\n" + "="*60)
    print("🎯 KEY TAKEAWAYS")
    print("="*60)
    
    print("1. 🗂️  完整观察保存在文件系统中，引用进入上下文")
    print("2. 🗜️  Recoverable compression maintains key information access")
    print("3. 💾 State externalization enables cross-session persistence")
    print("4. 📸 Memory snapshots provide backup and versioning")
    print("5. 🔍 Selective key preservation balances compression and accessibility")
    print("6. 🔄 Memory survives agent restarts and updates")
    
    print(f"\n💡 Efficiency Gains:")
    print(f"   - Context compression: Up to {(1 - stats.compression_ratio) * 100:.1f}% size reduction")
    print(f"   - External storage: Capacity depends on available disk space")
    print(f"   - Persistent state: Seamless session continuity")
    print(f"   - Selective access: Key data available without full restoration")
    
    # Cleanup
    memory1.cleanup()
    memory2.cleanup()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Filesystem Memory Demo")
    parser.add_argument("--demo", choices=["observations", "states", "persistence", "all"],
                       default="all", help="Type of demo to run")
    
    parser.add_argument("--workspace", help="Persistent directory for the persistence demonstration")
    parser.add_argument("--phase", choices=["save", "resume", "both"], default="both")
    args = parser.parse_args()
    if (args.workspace or args.phase != "both") and args.demo != "persistence":
        parser.error("--workspace 和 --phase 用于 --demo persistence。")
    
    if args.demo == "observations":
        memory = demonstrate_large_observation_handling()
        memory.cleanup()
    elif args.demo == "states":
        memory = demonstrate_state_persistence()
        memory.cleanup()
    elif args.demo == "persistence":
        try:
            demonstrate_cross_session_persistence(args.workspace, args.phase)
        except (ValueError, RuntimeError) as error:
            parser.exit(1, f"{error}\n")
    else:
        run_comprehensive_demo()
