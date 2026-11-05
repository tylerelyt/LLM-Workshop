#!/usr/bin/env python3
"""
Lesson 2: Tool Masking Strategy Demo

This demo showcases the "Mask, Don't Remove" principle for dynamic tool management.
Demonstrates state machine-driven tool availability and logits-level constraints.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


class AgentState(Enum):
    """Possible agent states that determine tool availability"""
    IDLE = "idle"
    FILE_OPERATIONS = "file_operations"
    WEB_BROWSING = "web_browsing"
    SYSTEM_ADMIN = "system_admin"
    RESEARCH_MODE = "research_mode"
    CODING_MODE = "coding_mode"
    COMMUNICATION = "communication"


@dataclass
class ToolDefinition:
    """Complete tool definition with masking metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]
    prefix: str
    category: str
    enabled: bool = True
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "enabled": self.enabled
        }


class ToolMaskingEngine:
    """
    Advanced tool masking implementation demonstrating:
    - State machine driven tool availability
    - Prefix-based tool grouping
    - Logits-level constraints
    - Context-aware masking rules
    """
    
    def __init__(self):
        self.current_state = AgentState.IDLE
        self.all_tools = self._initialize_tool_registry()
        self.masking_rules = self._define_masking_rules()
        self.state_history = []
        
    def _initialize_tool_registry(self) -> List[ToolDefinition]:
        """Initialize comprehensive tool registry with consistent prefixes"""
        return [
            # File operation tools
            ToolDefinition(
                name="file_read",
                description="Read contents of a file",
                parameters={"path": "string", "encoding": "string"},
                prefix="file_",
                category="filesystem"
            ),
            ToolDefinition(
                name="file_write", 
                description="Write content to a file",
                parameters={"path": "string", "content": "string", "mode": "string"},
                prefix="file_",
                category="filesystem"
            ),
            ToolDefinition(
                name="file_delete",
                description="Delete a file",
                parameters={"path": "string", "confirm": "boolean"},
                prefix="file_",
                category="filesystem"
            ),
            ToolDefinition(
                name="file_list",
                description="List files in a directory",
                parameters={"path": "string", "pattern": "string"},
                prefix="file_",
                category="filesystem"
            ),
            
            # Browser tools
            ToolDefinition(
                name="browser_navigate",
                description="Navigate to a URL",
                parameters={"url": "string", "wait_for": "string"},
                prefix="browser_",
                category="web"
            ),
            ToolDefinition(
                name="browser_click",
                description="Click an element on the page",
                parameters={"selector": "string", "wait": "boolean"},
                prefix="browser_",
                category="web"
            ),
            ToolDefinition(
                name="browser_extract",
                description="Extract text or data from page",
                parameters={"selector": "string", "attribute": "string"},
                prefix="browser_",
                category="web"
            ),
            ToolDefinition(
                name="browser_screenshot",
                description="Take a screenshot of the page",
                parameters={"path": "string", "full_page": "boolean"},
                prefix="browser_",
                category="web"
            ),
            
            # Shell/System tools
            ToolDefinition(
                name="shell_execute",
                description="Execute a shell command",
                parameters={"command": "string", "timeout": "number"},
                prefix="shell_",
                category="system"
            ),
            ToolDefinition(
                name="shell_cd",
                description="Change working directory", 
                parameters={"path": "string"},
                prefix="shell_",
                category="system"
            ),
            ToolDefinition(
                name="shell_env",
                description="Get or set environment variables",
                parameters={"action": "string", "variable": "string", "value": "string"},
                prefix="shell_",
                category="system"
            ),
            
            # Search tools
            ToolDefinition(
                name="search_web",
                description="Search the web for information",
                parameters={"query": "string", "num_results": "number"},
                prefix="search_",
                category="research"
            ),
            ToolDefinition(
                name="search_local",
                description="Search local files and documents",
                parameters={"query": "string", "path": "string", "file_types": "array"},
                prefix="search_",
                category="research"
            ),
            ToolDefinition(
                name="search_docs",
                description="Search documentation and help files",
                parameters={"query": "string", "source": "string"},
                prefix="search_",
                category="research"
            ),
            
            # Coding tools
            ToolDefinition(
                name="code_analyze",
                description="Analyze code structure and quality",
                parameters={"file_path": "string", "language": "string"},
                prefix="code_",
                category="development"
            ),
            ToolDefinition(
                name="code_format",
                description="Format code according to standards",
                parameters={"content": "string", "language": "string"},
                prefix="code_",
                category="development"
            ),
            ToolDefinition(
                name="code_test",
                description="Run tests for code",
                parameters={"test_path": "string", "test_type": "string"},
                prefix="code_",
                category="development"
            ),
            
            # Communication tools
            ToolDefinition(
                name="email_send",
                description="Send an email",
                parameters={"to": "string", "subject": "string", "body": "string"},
                prefix="email_",
                category="communication"
            ),
            ToolDefinition(
                name="slack_message",
                description="Send a Slack message",
                parameters={"channel": "string", "message": "string"},
                prefix="slack_",
                category="communication"  
            )
        ]
    
    def _define_masking_rules(self) -> Dict[AgentState, Dict[str, Any]]:
        """Define masking rules for different agent states"""
        return {
            AgentState.IDLE: {
                "allowed_prefixes": [],  # All tools available
                "blocked_prefixes": [],
                "description": "General purpose mode - all tools available"
            },
            AgentState.FILE_OPERATIONS: {
                "allowed_prefixes": ["file_"],
                "blocked_prefixes": ["browser_", "shell_", "email_", "slack_"],
                "description": "File operations only - no web browsing or system access"
            },
            AgentState.WEB_BROWSING: {
                "allowed_prefixes": ["browser_", "search_"],
                "blocked_prefixes": ["file_", "shell_", "code_"],
                "description": "Web browsing and search only"
            },
            AgentState.SYSTEM_ADMIN: {
                "allowed_prefixes": ["shell_", "file_"],
                "blocked_prefixes": ["browser_", "email_", "slack_"],
                "description": "System administration - shell and file access only"
            },
            AgentState.RESEARCH_MODE: {
                "allowed_prefixes": ["search_", "browser_", "file_"],
                "blocked_prefixes": ["shell_", "email_", "slack_"],
                "description": "Research mode - search and information gathering"
            },
            AgentState.CODING_MODE: {
                "allowed_prefixes": ["code_", "file_", "search_"],
                "blocked_prefixes": ["browser_", "shell_", "email_"],
                "description": "Development mode - coding tools and file access"
            },
            AgentState.COMMUNICATION: {
                "allowed_prefixes": ["email_", "slack_", "search_"],
                "blocked_prefixes": ["shell_", "file_", "code_"],
                "description": "Communication mode - messaging tools only"
            }
        }
    
    def transition_to_state(self, new_state: AgentState, context: str = "") -> None:
        """Transition agent to new state with context logging"""
        old_state = self.current_state
        self.current_state = new_state
        
        self.state_history.append({
            "from_state": old_state.value,
            "to_state": new_state.value,
            "context": context,
            "timestamp": "demo_timestamp"
        })
        
        print(f"🔄 State transition: {old_state.value} → {new_state.value}")
        if context:
            print(f"   Context: {context}")
    
    def get_available_tools(self, state: Optional[AgentState] = None) -> List[ToolDefinition]:
        """Get tools available in current or specified state"""
        target_state = state or self.current_state
        rules = self.masking_rules[target_state]
        
        available_tools = []
        for tool in self.all_tools:
            # Check if tool should be masked based on current rules
            should_mask = self._should_mask_tool(tool, rules)
            
            # Create a copy with updated enabled status
            tool_copy = ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
                prefix=tool.prefix,
                category=tool.category,
                enabled=not should_mask,
                usage_count=tool.usage_count
            )
            available_tools.append(tool_copy)
        
        return available_tools
    
    def _should_mask_tool(self, tool: ToolDefinition, rules: Dict[str, Any]) -> bool:
        """Determine if a tool should be masked based on current rules"""
        allowed_prefixes = rules.get("allowed_prefixes", [])
        blocked_prefixes = rules.get("blocked_prefixes", [])
        
        # If allowed_prefixes is empty, allow all except blocked
        if not allowed_prefixes:
            return any(tool.prefix.startswith(blocked) for blocked in blocked_prefixes)
        
        # If allowed_prefixes is specified, only allow those
        tool_allowed = any(tool.prefix.startswith(allowed) for allowed in allowed_prefixes)
        tool_blocked = any(tool.prefix.startswith(blocked) for blocked in blocked_prefixes)
        
        return not tool_allowed or tool_blocked
    
    def generate_tool_constraint(self, available_prefixes: List[str]) -> str:
        """Generate logits constraint for function calling"""
        if not available_prefixes:
            return '{"tool_call": {"name": "'
        
        # Create regex pattern for allowed prefixes
        prefix_pattern = '|'.join(f'{prefix}' for prefix in available_prefixes)
        constraint = f'{{"tool_call": {{"name": "({prefix_pattern})'
        
        return constraint
    
    def demonstrate_state_transitions(self) -> None:
        """Demonstrate how state transitions affect tool availability"""
        print("🎭 === State Transition Demo ===\n")
        
        scenarios = [
            (AgentState.IDLE, "Starting in general mode"),
            (AgentState.FILE_OPERATIONS, "User requests file management"),
            (AgentState.WEB_BROWSING, "User wants to browse websites"),
            (AgentState.SYSTEM_ADMIN, "System maintenance required"),
            (AgentState.RESEARCH_MODE, "Research task initiated"),
            (AgentState.CODING_MODE, "Development work begins"),
            (AgentState.COMMUNICATION, "Need to send messages"),
            (AgentState.IDLE, "Return to general mode")
        ]
        
        for state, context in scenarios:
            self.transition_to_state(state, context)
            tools = self.get_available_tools()
            enabled_tools = [t for t in tools if t.enabled]
            masked_tools = [t for t in tools if not t.enabled]
            
            print(f"📋 State: {state.value.upper()}")
            print(f"   Description: {self.masking_rules[state]['description']}")
            print(f"   ✅ Enabled ({len(enabled_tools)}): {[t.name for t in enabled_tools]}")
            print(f"   🚫 Masked ({len(masked_tools)}): {[t.name for t in masked_tools]}")
            
            # Show logits constraint
            enabled_prefixes = list(set(t.prefix for t in enabled_tools))
            constraint = self.generate_tool_constraint(enabled_prefixes)
            print(f"   🎯 Logits constraint: {constraint}...")
            print()
    
    def analyze_masking_efficiency(self) -> Dict[str, Any]:
        """Analyze the efficiency of the masking strategy"""
        total_tools = len(self.all_tools)
        analysis = {}
        
        for state in AgentState:
            tools = self.get_available_tools(state)
            enabled = len([t for t in tools if t.enabled])
            masked = len([t for t in tools if not t.enabled])
            
            analysis[state.value] = {
                "total_tools": total_tools,
                "enabled_tools": enabled,
                "masked_tools": masked,
                "masking_percentage": (masked / total_tools) * 100,
                "focus_ratio": enabled / total_tools
            }
        
        return analysis
    
    def simulate_context_pollution_comparison(self) -> None:
        """Demonstrate context pollution with and without masking"""
        print("🧪 === Context Pollution Comparison ===\n")
        
        # Scenario: File operation task
        user_request = "I need to read a configuration file and update it"
        
        print(f"User Request: {user_request}\n")
        
        # Without masking (bad)
        print("❌ WITHOUT MASKING (Context Pollution):")
        all_tools_context = "Available tools:\n"
        for tool in self.all_tools:
            all_tools_context += f"- {tool.name}: {tool.description}\n"
        
        print(f"Context size: {len(all_tools_context)} characters")
        print(f"Tool choices: {len(self.all_tools)} (overwhelming!)")
        print("Issues: Context pollution, poor tool selection, cache misses\n")
        
        # With masking (good)
        print("✅ WITH MASKING (Clean Context):")
        self.transition_to_state(AgentState.FILE_OPERATIONS, "File operation detected")
        available_tools = [t for t in self.get_available_tools() if t.enabled]
        
        masked_context = "Available tools:\n"
        for tool in available_tools:
            masked_context += f"- {tool.name}: {tool.description}\n"
        
        print(f"Context size: {len(masked_context)} characters")
        print(f"Tool choices: {len(available_tools)} (focused!)")
        print("Benefits: Clean context, better tool selection, cache efficiency")
        
        reduction = ((len(all_tools_context) - len(masked_context)) / len(all_tools_context)) * 100
        print(f"Context reduction: {reduction:.1f}%")


def run_comprehensive_demo():
    """Run comprehensive tool masking demonstration"""
    print("🛠️ Tool Masking Strategy & Dynamic Behavior Control Demo\n")
    
    engine = ToolMaskingEngine()
    
    # Demo 1: State transitions and tool availability
    engine.demonstrate_state_transitions()
    
    print("="*60)
    print("📊 MASKING EFFICIENCY ANALYSIS")
    print("="*60)
    
    # Demo 2: Efficiency analysis
    analysis = engine.analyze_masking_efficiency()
    
    for state, metrics in analysis.items():
        print(f"\nState: {state.upper()}")
        print(f"  Tools enabled: {metrics['enabled_tools']}/{metrics['total_tools']}")
        print(f"  Masking rate: {metrics['masking_percentage']:.1f}%")
        print(f"  Focus ratio: {metrics['focus_ratio']:.2f}")
    
    print("\n" + "="*60)
    print("🧪 CONTEXT POLLUTION DEMO")
    print("="*60)
    
    # Demo 3: Context pollution comparison
    engine.simulate_context_pollution_comparison()
    
    print("\n" + "="*60)
    print("🎯 KEY TAKEAWAYS")
    print("="*60)
    
    print("1. 🛡️  Tool masking prevents context pollution")
    print("2. 🎯 State-based masking improves focus and decision quality")
    print("3. 💾 Consistent tool definitions maintain cache efficiency")
    print("4. ⚡ Prefix-based grouping enables efficient batch control")
    print("5. 🎭 State machines provide predictable tool management")
    print("6. 🔧 Logits constraints enable precise behavior control")
    
    # Show prefix grouping benefits
    print("\n📦 Prefix Grouping Benefits:")
    prefixes = {}
    for tool in engine.all_tools:
        if tool.prefix not in prefixes:
            prefixes[tool.prefix] = []
        prefixes[tool.prefix].append(tool.name)
    
    for prefix, tools in prefixes.items():
        print(f"  {prefix}* : {len(tools)} tools ({', '.join(tools)})")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tool Masking Strategy Demo")
    parser.add_argument("--demo", choices=["transitions", "analysis", "pollution", "all"],
                       default="all", help="Type of demo to run")
    
    args = parser.parse_args()
    
    engine = ToolMaskingEngine()
    
    if args.demo == "transitions":
        engine.demonstrate_state_transitions()
    elif args.demo == "analysis":
        analysis = engine.analyze_masking_efficiency()
        for state, metrics in analysis.items():
            print(f"{state}: {metrics['enabled_tools']} tools enabled")
    elif args.demo == "pollution":
        engine.simulate_context_pollution_comparison()
    else:
        run_comprehensive_demo() 