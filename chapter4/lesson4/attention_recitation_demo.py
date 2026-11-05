#!/usr/bin/env python3
"""
Lesson 4: Attention Recitation Demo

This demo showcases attention manipulation through recitation mechanisms.
Demonstrates todo.md generation, goal focus maintenance, and attention bias techniques.
"""

import json
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


@dataclass
class TaskProgress:
    """Track progress of individual tasks"""
    id: str
    description: str
    status: str  # pending, in_progress, completed, blocked
    priority: int  # 1-5, 1 being highest
    estimated_effort: str
    dependencies: List[str]
    notes: str = ""
    completed_at: Optional[str] = None


@dataclass
class AttentionMetrics:
    """Metrics for attention management effectiveness"""
    total_tasks: int = 0
    completed_tasks: int = 0
    tasks_on_track: int = 0
    attention_refocus_count: int = 0
    goal_drift_incidents: int = 0
    
    @property
    def completion_rate(self) -> float:
        return self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0.0
    
    @property
    def focus_effectiveness(self) -> float:
        return self.tasks_on_track / self.total_tasks if self.total_tasks > 0 else 0.0


class AttentionRecitationEngine:
    """
    Advanced attention management implementation demonstrating:
    - Dynamic todo.md generation and maintenance
    - Goal focus injection and reinforcement
    - Lost-in-the-middle prevention
    - Multi-level attention hierarchy
    """
    
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or tempfile.mkdtemp(prefix="attention_workspace_"))
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_todo_file = None
        self.main_objective = ""
        self.tasks: List[TaskProgress] = []
        self.attention_history = []
        self.metrics = AttentionMetrics()
        
    def initialize_project(self, main_objective: str, task_descriptions: List[str],
                          priorities: Optional[List[int]] = None) -> str:
        """Initialize a new project with main objective and task breakdown"""
        self.main_objective = main_objective
        self.tasks = []
        
        priorities = priorities or [3] * len(task_descriptions)  # Default medium priority
        
        # Create task objects
        for i, (desc, priority) in enumerate(zip(task_descriptions, priorities)):
            task = TaskProgress(
                id=f"task_{i+1:02d}",
                description=desc,
                status="pending",
                priority=priority,
                estimated_effort="TBD",
                dependencies=[]
            )
            self.tasks.append(task)
        
        self.metrics.total_tasks = len(self.tasks)
        
        # Set first task as in_progress
        if self.tasks:
            self.tasks[0].status = "in_progress"
            self.metrics.tasks_on_track = 1
        
        # Generate initial todo.md
        todo_content = self._generate_todo_content()
        self.active_todo_file = self.workspace_dir / "todo.md"
        
        with open(self.active_todo_file, 'w') as f:
            f.write(todo_content)
        
        print(f"🎯 Initialized project: {main_objective}")
        print(f"📋 Created {len(self.tasks)} tasks in todo.md")
        print(f"🔄 First task in progress: {self.tasks[0].description}")
        
        return todo_content
    
    def _generate_todo_content(self) -> str:
        """Generate comprehensive todo.md content with attention anchors"""
        content_parts = [
            "# Project Progress Tracker",
            "",
            "## 🎯 MAIN OBJECTIVE",
            f"**{self.main_objective}**",
            "",
            "## 📋 Task Breakdown",
            ""
        ]
        
        # Group tasks by status
        status_groups = {
            "in_progress": "🔄 In Progress",
            "pending": "⏳ Pending", 
            "completed": "✅ Completed",
            "blocked": "🚫 Blocked"
        }
        
        for status, header in status_groups.items():
            tasks_in_status = [t for t in self.tasks if t.status == status]
            if tasks_in_status:
                content_parts.append(f"### {header}")
                content_parts.append("")
                
                for task in sorted(tasks_in_status, key=lambda t: t.priority):
                    priority_indicator = "🔥" * task.priority if task.priority <= 2 else ""
                    content_parts.append(f"- **{task.id}**: {task.description} {priority_indicator}")
                    if task.notes:
                        content_parts.append(f"  *Notes: {task.notes}*")
                    if task.dependencies:
                        content_parts.append(f"  *Depends on: {', '.join(task.dependencies)}*")
                content_parts.append("")
        
        # Progress statistics
        completed_count = len([t for t in self.tasks if t.status == "completed"])
        in_progress_count = len([t for t in self.tasks if t.status == "in_progress"])
        
        content_parts.extend([
            "## 📊 Progress Overview",
            "",
            f"- **Total Tasks**: {len(self.tasks)}",
            f"- **Completed**: {completed_count} ({completed_count/len(self.tasks)*100:.1f}%)",
            f"- **In Progress**: {in_progress_count}",
            f"- **Remaining**: {len(self.tasks) - completed_count - in_progress_count}",
            "",
            "## 🎯 CURRENT FOCUS",
            ""
        ])
        
        # Current focus section (attention anchor)
        current_task = next((t for t in self.tasks if t.status == "in_progress"), None)
        if current_task:
            content_parts.extend([
                f"**ACTIVE TASK**: {current_task.description}",
                f"**Task ID**: {current_task.id}",
                f"**Priority**: {'🔥' * current_task.priority}",
                ""
            ])
            
            # Next tasks
            next_tasks = [t for t in self.tasks if t.status == "pending"][:3]
            if next_tasks:
                content_parts.extend([
                    "**NEXT UP**:",
                    ""
                ])
                for task in next_tasks:
                    content_parts.append(f"- {task.description}")
                content_parts.append("")
        
        # Attention reinforcement section
        content_parts.extend([
            "---",
            "## ⚠️ ATTENTION REINFORCEMENT",
            "",
            f"🎯 **PRIMARY GOAL**: {self.main_objective}",
            "",
            "**STAY FOCUSED ON**:",
            f"- Current active task: {current_task.description if current_task else 'None'}",
            "- Maintaining progress toward main objective",
            "- Not getting sidetracked by unrelated requests",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return "\n".join(content_parts)
    
    def complete_task(self, task_id: str, notes: str = "") -> str:
        """Mark a task as completed and update focus"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return f"❌ Task {task_id} not found"
        
        if task.status != "in_progress":
            return f"⚠️  Task {task_id} is not currently in progress"
        
        # Mark as completed
        task.status = "completed"
        task.completed_at = datetime.now().isoformat()
        task.notes = notes
        
        self.metrics.completed_tasks += 1
        
        # Find next task to start
        next_task = None
        for t in self.tasks:
            if t.status == "pending":
                # Check if dependencies are met
                deps_met = all(
                    any(dep_task.id == dep and dep_task.status == "completed" 
                        for dep_task in self.tasks)
                    for dep in t.dependencies
                ) if t.dependencies else True
                
                if deps_met:
                    next_task = t
                    break
        
        if next_task:
            next_task.status = "in_progress"
            self.metrics.tasks_on_track += 1
        
        # Update todo.md
        self._update_todo_file()
        
        print(f"✅ Completed task: {task.description}")
        if next_task:
            print(f"🔄 Started next task: {next_task.description}")
        
        return self._get_updated_todo_content()
    
    def inject_attention_focus(self, context: str, include_progress: bool = True) -> str:
        """Inject attention focus into any context to prevent drift"""
        current_task = next((t for t in self.tasks if t.status == "in_progress"), None)
        
        attention_injection = [
            "",
            "--- ATTENTION FOCUS INJECTION ---",
            f"🎯 PRIMARY OBJECTIVE: {self.main_objective}",
            ""
        ]
        
        if current_task:
            attention_injection.extend([
                f"🔄 CURRENT ACTIVE TASK: {current_task.description}",
                f"   Task ID: {current_task.id}",
                f"   Priority: {'High' if current_task.priority <= 2 else 'Medium' if current_task.priority <= 3 else 'Low'}",
                ""
            ])
        
        if include_progress:
            completed = len([t for t in self.tasks if t.status == "completed"])
            total = len(self.tasks)
            progress_pct = (completed / total * 100) if total > 0 else 0
            
            attention_injection.extend([
                f"📊 PROGRESS: {completed}/{total} tasks completed ({progress_pct:.1f}%)",
                ""
            ])
        
        attention_injection.extend([
            "⚠️  REMINDER: Stay focused on current task and main objective",
            "❌ AVOID: Getting sidetracked by unrelated requests or topics",
            "--- END ATTENTION FOCUS ---",
            ""
        ])
        
        self.attention_history.append({
            "timestamp": datetime.now().isoformat(),
            "context_length": len(context),
            "injection_length": len("\n".join(attention_injection)),
            "current_task": current_task.id if current_task else None
        })
        
        self.metrics.attention_refocus_count += 1
        
        return context + "\n".join(attention_injection)
    
    def detect_goal_drift(self, user_input: str, response_plan: str) -> Dict[str, Any]:
        """Detect potential goal drift in user input or planned response"""
        drift_indicators = {
            "off_topic_keywords": [
                "unrelated", "different topic", "change subject", "something else",
                "by the way", "random question", "quick question"
            ],
            "scope_expansion": [
                "also do", "additionally", "while we're at it", "might as well",
                "expand scope", "add feature", "include"
            ],
            "task_switching": [
                "switch to", "move on to", "work on instead", "focus on different",
                "abandon current", "stop working on"
            ]
        }
        
        drift_score = 0
        detected_patterns = []
        
        combined_text = (user_input + " " + response_plan).lower()
        
        for category, keywords in drift_indicators.items():
            matches = [kw for kw in keywords if kw in combined_text]
            if matches:
                drift_score += len(matches)
                detected_patterns.append({
                    "category": category,
                    "matches": matches,
                    "severity": len(matches)
                })
        
        is_drift = drift_score > 2  # Threshold for significant drift
        
        if is_drift:
            self.metrics.goal_drift_incidents += 1
        
        return {
            "is_drift_detected": is_drift,
            "drift_score": drift_score,
            "patterns": detected_patterns,
            "recommendation": self._get_drift_mitigation(is_drift, detected_patterns)
        }
    
    def _get_drift_mitigation(self, is_drift: bool, patterns: List[Dict]) -> str:
        """Get recommendation for handling detected drift"""
        if not is_drift:
            return "No drift detected. Continue with current focus."
        
        mitigation_strategies = []
        
        for pattern in patterns:
            if pattern["category"] == "off_topic_keywords":
                mitigation_strategies.append(
                    "Acknowledge the off-topic request but redirect to current task"
                )
            elif pattern["category"] == "scope_expansion":
                mitigation_strategies.append(
                    "Note the additional request for later; maintain current scope"
                )
            elif pattern["category"] == "task_switching":
                mitigation_strategies.append(
                    "Confirm task switch is intentional; update todo.md if necessary"
                )
        
        return "; ".join(set(mitigation_strategies))
    
    def _update_todo_file(self):
        """Update the todo.md file with current state"""
        if self.active_todo_file:
            content = self._generate_todo_content()
            with open(self.active_todo_file, 'w') as f:
                f.write(content)
    
    def _get_updated_todo_content(self) -> str:
        """Get current todo.md content"""
        return self._generate_todo_content()
    
    def get_attention_report(self) -> Dict[str, Any]:
        """Get comprehensive attention management report"""
        return {
            "metrics": {
                "total_tasks": self.metrics.total_tasks,
                "completed_tasks": self.metrics.completed_tasks,
                "completion_rate": f"{self.metrics.completion_rate:.2%}",
                "focus_effectiveness": f"{self.metrics.focus_effectiveness:.2%}",
                "attention_refocus_count": self.metrics.attention_refocus_count,
                "goal_drift_incidents": self.metrics.goal_drift_incidents
            },
            "current_focus": {
                "main_objective": self.main_objective,
                "active_task": next((t.description for t in self.tasks if t.status == "in_progress"), None),
                "tasks_remaining": len([t for t in self.tasks if t.status != "completed"])
            },
            "attention_history": self.attention_history[-5:],  # Last 5 injections
            "workspace": str(self.workspace_dir)
        }


def demonstrate_todo_generation():
    """Demonstrate dynamic todo.md generation and maintenance"""
    print("📋 === Todo Generation & Maintenance Demo ===\n")
    
    engine = AttentionRecitationEngine()
    
    # Complex web application project
    main_goal = "Build a complete e-commerce web application with user authentication"
    tasks = [
        "Set up development environment and project structure",
        "Design database schema for users, products, and orders",
        "Implement user registration and authentication system",
        "Create product catalog with search and filtering",
        "Build shopping cart functionality",
        "Implement secure payment processing",
        "Add order management and tracking",
        "Create admin dashboard for inventory management", 
        "Implement email notifications for orders",
        "Add comprehensive testing suite",
        "Deploy to production environment",
        "Set up monitoring and logging"
    ]
    
    priorities = [1, 2, 1, 2, 2, 1, 3, 3, 4, 2, 1, 3]  # 1=high, 5=low
    
    # Initialize project
    initial_todo = engine.initialize_project(main_goal, tasks, priorities)
    
    print("Initial todo.md content:")
    print("=" * 40)
    print(initial_todo[:500] + "...\n")
    
    # Simulate task completion
    print("--- Simulating Task Progression ---")
    
    # Complete first few tasks
    tasks_to_complete = [
        ("task_01", "Created React app, configured TypeScript, set up Git repo"),
        ("task_02", "Designed PostgreSQL schema with proper relationships"),
        ("task_03", "Implemented JWT authentication with bcrypt password hashing")
    ]
    
    for task_id, notes in tasks_to_complete:
        updated_todo = engine.complete_task(task_id, notes)
        print()
    
    print("--- Final Todo State ---")
    final_todo = engine._get_updated_todo_content()
    print(final_todo[:600] + "...\n")
    
    return engine


def demonstrate_attention_injection():
    """Demonstrate attention focus injection to prevent drift"""
    print("🎯 === Attention Focus Injection Demo ===\n")
    
    engine = AttentionRecitationEngine()
    
    # Set up a project
    engine.initialize_project(
        "Create automated testing framework for web applications",
        [
            "Research existing testing frameworks and tools",
            "Design framework architecture and API",
            "Implement core testing engine",
            "Add browser automation capabilities",
            "Create reporting and visualization features"
        ]
    )
    
    # Simulate various contexts where attention injection is needed
    contexts = [
        {
            "name": "Long technical discussion",
            "context": """User has been discussing web testing approaches for 20 minutes.
The conversation has covered Selenium, Playwright, Cypress, and custom solutions.
We've talked about pros and cons of each approach, performance considerations,
and integration with CI/CD pipelines. The discussion is getting quite detailed
and we might be losing sight of the main objective..."""
        },
        {
            "name": "Potential scope creep",
            "context": """User asks: 'This testing framework is great, but could we also add
mobile app testing? And maybe API testing too? Oh, and performance testing
would be really useful. Actually, while we're at it, could we include
security testing features as well?'"""
        },
        {
            "name": "Task switching request",
            "context": """User says: 'Actually, I just remembered I need to work on something
else first. Can we pause the testing framework and help me build a 
data visualization dashboard instead? It's more urgent right now.'"""
        }
    ]
    
    for i, ctx in enumerate(contexts, 1):
        print(f"--- Context {i}: {ctx['name']} ---")
        
        # Inject attention focus
        focused_context = engine.inject_attention_focus(ctx['context'])
        
        # Show the injection (last part of the context)
        injection_start = focused_context.find("--- ATTENTION FOCUS INJECTION ---")
        if injection_start != -1:
            injection = focused_context[injection_start:]
            print("Attention injection added:")
            print(injection)
        
        # Demonstrate drift detection
        drift_analysis = engine.detect_goal_drift(ctx['context'], "")
        print(f"\nDrift Analysis:")
        print(f"  Drift detected: {drift_analysis['is_drift_detected']}")
        print(f"  Drift score: {drift_analysis['drift_score']}")
        print(f"  Recommendation: {drift_analysis['recommendation']}")
        print()
    
    return engine


def demonstrate_multi_level_attention():
    """Demonstrate multi-level attention hierarchy"""
    print("🎭 === Multi-Level Attention Hierarchy Demo ===\n")
    
    engine = AttentionRecitationEngine()
    
    # Complex project with dependencies
    engine.initialize_project(
        "Develop AI-powered customer service chatbot platform",
        [
            "Research NLP libraries and frameworks",
            "Set up machine learning pipeline infrastructure", 
            "Train initial intent classification model",
            "Implement conversation flow engine",
            "Create knowledge base management system",
            "Build chat interface and integration APIs",
            "Add analytics and monitoring dashboard",
            "Implement A/B testing framework for responses",
            "Create admin tools for conversation training",
            "Deploy and scale production system"
        ],
        [1, 1, 2, 2, 3, 2, 3, 4, 3, 1]
    )
    
    # Add task dependencies
    engine.tasks[2].dependencies = ["task_01", "task_02"]  # Model training needs research and infrastructure
    engine.tasks[3].dependencies = ["task_03"]  # Conversation engine needs model
    engine.tasks[5].dependencies = ["task_04"]  # Chat interface needs conversation engine
    
    print("--- Project with Dependencies ---")
    print(f"Main Goal: {engine.main_objective}")
    print("Task Dependencies:")
    for task in engine.tasks:
        if task.dependencies:
            print(f"  {task.id}: {task.description[:50]}... (depends on: {', '.join(task.dependencies)})")
    
    print("\n--- Attention Levels ---")
    
    # Level 1: Main objective (highest level)
    print("🎯 LEVEL 1 - Strategic Focus:")
    print(f"   {engine.main_objective}")
    
    # Level 2: Current phase/milestone  
    current_task = next((t for t in engine.tasks if t.status == "in_progress"), None)
    if current_task:
        print("🔄 LEVEL 2 - Tactical Focus:")
        print(f"   {current_task.description}")
    
    # Level 3: Immediate action items
    print("⚡ LEVEL 3 - Operational Focus:")
    print("   - Research TensorFlow vs PyTorch for NLP")
    print("   - Compare Rasa, Dialogflow, and custom solutions")
    print("   - Set up development environment")
    
    # Show how attention hierarchy helps prevent drift
    print("\n--- Drift Prevention Through Hierarchy ---")
    
    drift_scenarios = [
        "User asks about completely different project",
        "Request to add unrelated features", 
        "Suggestion to change core technology stack",
        "Question about unrelated company processes"
    ]
    
    for scenario in drift_scenarios:
        print(f"\nScenario: {scenario}")
        print("Response strategy:")
        print("  1. Acknowledge request (Level 3)")
        print("  2. Check alignment with current task (Level 2)")
        print("  3. Verify consistency with main objective (Level 1)")
        print("  4. Decide: address now, defer, or redirect")
    
    return engine


def run_comprehensive_demo():
    """Run comprehensive attention recitation demonstration"""
    print("🎯 Attention Recitation & Goal Focus Management Demo\n")
    
    # Demo 1: Todo generation and maintenance
    engine1 = demonstrate_todo_generation()
    
    # Demo 2: Attention injection
    engine2 = demonstrate_attention_injection()
    
    # Demo 3: Multi-level attention hierarchy
    engine3 = demonstrate_multi_level_attention()
    
    print("\n" + "="*60)
    print("📊 ATTENTION MANAGEMENT ANALYSIS")
    print("="*60)
    
    # Combine reports from all engines
    reports = [engine1.get_attention_report(), engine2.get_attention_report(), engine3.get_attention_report()]
    
    total_refocus = sum(int(r["metrics"]["attention_refocus_count"]) for r in reports)
    total_drift = sum(int(r["metrics"]["goal_drift_incidents"]) for r in reports)
    
    print(f"Total Attention Refocus Events: {total_refocus}")
    print(f"Total Goal Drift Incidents: {total_drift}")
    print(f"Drift Prevention Rate: {((total_refocus - total_drift) / total_refocus * 100):.1f}%")
    
    print("\n" + "="*60)
    print("🎯 KEY TAKEAWAYS")
    print("="*60)
    
    print("1. 📋 Dynamic todo.md keeps goals visible and current")
    print("2. 🎯 Attention injection prevents lost-in-the-middle problems")
    print("3. 🎭 Multi-level hierarchy provides structured focus")
    print("4. 🔍 Drift detection enables proactive refocusing")
    print("5. 📊 Progress tracking maintains motivation and direction")
    print("6. ⚠️  Regular recitation reinforces primary objectives")
    
    print(f"\n💡 Effectiveness Metrics:")
    avg_completion = sum(float(r["metrics"]["completion_rate"].rstrip('%')) for r in reports) / len(reports)
    print(f"   - Average task completion rate: {avg_completion:.1f}%")
    print(f"   - Attention management interventions: {total_refocus}")
    print(f"   - Successful drift prevention: {total_refocus - total_drift}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Attention Recitation Demo")
    parser.add_argument("--demo", choices=["todo", "injection", "hierarchy", "all"],
                       default="all", help="Type of demo to run")
    
    args = parser.parse_args()
    
    if args.demo == "todo":
        demonstrate_todo_generation()
    elif args.demo == "injection":
        demonstrate_attention_injection()
    elif args.demo == "hierarchy":
        demonstrate_multi_level_attention()
    else:
        run_comprehensive_demo() 