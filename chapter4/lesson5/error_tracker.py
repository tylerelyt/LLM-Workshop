#!/usr/bin/env python3
"""
Error Tracker & Failure Learning Demo
错误轨迹记录和失败学习演示

实现Manus的"Keep the Wrong Stuff In"理念，将错误作为学习资源。
"""

import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib


class ErrorType(Enum):
    """错误分类枚举"""
    ENVIRONMENT = "environment"      # 环境错误（网络、API等）
    LOGIC = "logic"                 # 逻辑错误（参数、计算等）
    SEMANTIC = "semantic"           # 语义错误（任务理解等）
    RESOURCE = "resource"           # 资源错误（内存、存储等）
    PERMISSION = "permission"       # 权限错误
    TIMEOUT = "timeout"            # 超时错误


class RecoveryStrategy(Enum):
    """恢复策略枚举"""
    RETRY = "retry"                # 重试
    SKIP = "skip"                  # 跳过
    ALTERNATIVE = "alternative"     # 替代方案
    ABORT = "abort"                # 中止
    WAIT_RETRY = "wait_retry"      # 等待后重试


@dataclass
class ActionRecord:
    """行动记录"""
    tool: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ErrorRecord:
    """错误记录"""
    error_type: ErrorType
    error_code: str
    message: str
    action: ActionRecord
    context: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_attempts: List[Dict] = field(default_factory=list)
    resolved: bool = False
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['error_type'] = self.error_type.value
        data['timestamp'] = self.timestamp.isoformat()
        data['action']['timestamp'] = self.action.timestamp.isoformat()
        return data
    
    def get_signature(self) -> str:
        """获取错误签名，用于识别相似错误"""
        sig_data = f"{self.action.tool}:{self.error_code}:{self.error_type.value}"
        return hashlib.md5(sig_data.encode()).hexdigest()[:8]


@dataclass
class RecoveryAttempt:
    """恢复尝试记录"""
    strategy: RecoveryStrategy
    action: ActionRecord
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['strategy'] = self.strategy.value
        data['timestamp'] = self.timestamp.isoformat()
        data['action']['timestamp'] = self.action.timestamp.isoformat()
        return data


class ErrorTracker:
    """错误跟踪器 - 记录和分析Agent的错误模式"""
    
    def __init__(self, storage_path: str = "error_history.json"):
        self.storage_path = storage_path
        self.error_history: List[ErrorRecord] = []
        self.success_patterns: Dict[str, int] = {}
        self.failure_patterns: Dict[str, int] = {}
        self.load_history()
    
    def track_error(self, 
                   error_type: ErrorType,
                   error_code: str,
                   message: str,
                   action: ActionRecord,
                   context: Dict[str, Any] = None,
                   stack_trace: str = None) -> ErrorRecord:
        """记录新错误"""
        error_record = ErrorRecord(
            error_type=error_type,
            error_code=error_code,
            message=message,
            action=action,
            context=context or {},
            stack_trace=stack_trace
        )
        
        self.error_history.append(error_record)
        self._update_failure_patterns(error_record)
        self.save_history()
        
        print(f"❌ [ERROR TRACKED] {error_type.value}: {error_code}")
        print(f"   Action: {action.tool}({action.parameters})")
        print(f"   Message: {message}")
        print(f"   Signature: {error_record.get_signature()}")
        
        return error_record
    
    def track_recovery(self, 
                      error_record: ErrorRecord,
                      strategy: RecoveryStrategy,
                      action: ActionRecord,
                      success: bool,
                      notes: str = "") -> RecoveryAttempt:
        """记录恢复尝试"""
        recovery = RecoveryAttempt(
            strategy=strategy,
            action=action,
            success=success,
            notes=notes
        )
        
        error_record.recovery_attempts.append(recovery.to_dict())
        if success:
            error_record.resolved = True
            self._update_success_patterns(error_record, recovery)
        
        self.save_history()
        
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"🔄 [RECOVERY {status}] Strategy: {strategy.value}")
        print(f"   Action: {action.tool}({action.parameters})")
        if notes:
            print(f"   Notes: {notes}")
        
        return recovery
    
    def find_similar_errors(self, error_record: ErrorRecord, limit: int = 5) -> List[ErrorRecord]:
        """查找相似的历史错误"""
        signature = error_record.get_signature()
        similar = []
        
        for err in self.error_history:
            if err != error_record and err.get_signature() == signature:
                similar.append(err)
        
        # 按时间排序，最新的在前
        similar.sort(key=lambda x: x.timestamp, reverse=True)
        return similar[:limit]
    
    def get_success_rate(self, tool: str = None, error_type: ErrorType = None) -> float:
        """获取成功恢复率"""
        filtered_errors = self._filter_errors(tool=tool, error_type=error_type)
        
        if not filtered_errors:
            return 0.0
        
        resolved_count = sum(1 for err in filtered_errors if err.resolved)
        return resolved_count / len(filtered_errors)
    
    def get_error_frequency(self, days: int = 7) -> Dict[str, int]:
        """获取错误频率统计"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_errors = [err for err in self.error_history if err.timestamp >= cutoff_date]
        
        frequency = {}
        for err in recent_errors:
            key = f"{err.action.tool}:{err.error_code}"
            frequency[key] = frequency.get(key, 0) + 1
        
        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """分析错误模式"""
        total_errors = len(self.error_history)
        resolved_errors = sum(1 for err in self.error_history if err.resolved)
        
        # 错误类型分布
        type_distribution = {}
        for err in self.error_history:
            type_name = err.error_type.value
            type_distribution[type_name] = type_distribution.get(type_name, 0) + 1
        
        # 工具错误率
        tool_errors = {}
        for err in self.error_history:
            tool = err.action.tool
            tool_errors[tool] = tool_errors.get(tool, 0) + 1
        
        # 恢复策略效果
        strategy_success = {}
        for err in self.error_history:
            for attempt in err.recovery_attempts:
                strategy = attempt['strategy']
                if strategy not in strategy_success:
                    strategy_success[strategy] = {'total': 0, 'success': 0}
                strategy_success[strategy]['total'] += 1
                if attempt['success']:
                    strategy_success[strategy]['success'] += 1
        
        # 计算成功率
        for strategy in strategy_success:
            total = strategy_success[strategy]['total']
            success = strategy_success[strategy]['success']
            strategy_success[strategy]['success_rate'] = success / total if total > 0 else 0
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_errors,
            'overall_recovery_rate': resolved_errors / total_errors if total_errors > 0 else 0,
            'error_type_distribution': type_distribution,
            'tool_error_frequency': tool_errors,
            'recovery_strategy_effectiveness': strategy_success,
            'recent_error_trends': self.get_error_frequency()
        }
    
    def _filter_errors(self, tool: str = None, error_type: ErrorType = None) -> List[ErrorRecord]:
        """过滤错误记录"""
        filtered = self.error_history
        
        if tool:
            filtered = [err for err in filtered if err.action.tool == tool]
        
        if error_type:
            filtered = [err for err in filtered if err.error_type == error_type]
        
        return filtered
    
    def _update_failure_patterns(self, error_record: ErrorRecord):
        """更新失败模式"""
        pattern_key = f"{error_record.action.tool}:{error_record.error_type.value}"
        self.failure_patterns[pattern_key] = self.failure_patterns.get(pattern_key, 0) + 1
    
    def _update_success_patterns(self, error_record: ErrorRecord, recovery: RecoveryAttempt):
        """更新成功模式"""
        pattern_key = f"{error_record.action.tool}:{recovery.strategy.value}"
        self.success_patterns[pattern_key] = self.success_patterns.get(pattern_key, 0) + 1
    
    def save_history(self):
        """保存错误历史"""
        try:
            data = {
                'error_history': [err.to_dict() for err in self.error_history],
                'success_patterns': self.success_patterns,
                'failure_patterns': self.failure_patterns,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Failed to save error history: {e}")
    
    def load_history(self):
        """加载错误历史"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建错误记录对象
            for err_data in data.get('error_history', []):
                action_data = err_data['action']
                action = ActionRecord(
                    tool=action_data['tool'],
                    parameters=action_data['parameters'],
                    timestamp=datetime.fromisoformat(action_data['timestamp'])
                )
                
                error_record = ErrorRecord(
                    error_type=ErrorType(err_data['error_type']),
                    error_code=err_data['error_code'],
                    message=err_data['message'],
                    action=action,
                    context=err_data.get('context', {}),
                    stack_trace=err_data.get('stack_trace'),
                    timestamp=datetime.fromisoformat(err_data['timestamp']),
                    recovery_attempts=err_data.get('recovery_attempts', []),
                    resolved=err_data.get('resolved', False)
                )
                
                self.error_history.append(error_record)
            
            self.success_patterns = data.get('success_patterns', {})
            self.failure_patterns = data.get('failure_patterns', {})
            
        except FileNotFoundError:
            print("📁 No existing error history found, starting fresh.")
        except Exception as e:
            print(f"⚠️  Failed to load error history: {e}")


def create_demo_scenarios():
    """创建演示场景"""
    tracker = ErrorTracker("demo_error_history.json")
    
    print("🧪 Creating demo error scenarios...\n")
    
    # 场景1: 文件操作错误
    action1 = ActionRecord(
        tool="file_read",
        parameters={"path": "/nonexistent/file.txt"}
    )
    error1 = tracker.track_error(
        error_type=ErrorType.ENVIRONMENT,
        error_code="FileNotFoundError",
        message="No such file or directory: '/nonexistent/file.txt'",
        action=action1,
        context={"operation": "read_config", "user": "demo"}
    )
    
    # 恢复尝试1: 检查文件存在性
    recovery_action1 = ActionRecord(
        tool="file_exists",
        parameters={"path": "/nonexistent/file.txt"}
    )
    tracker.track_recovery(
        error_record=error1,
        strategy=RecoveryStrategy.ALTERNATIVE,
        action=recovery_action1,
        success=True,
        notes="Switched to checking file existence first"
    )
    
    # 场景2: API限速错误
    action2 = ActionRecord(
        tool="api_call",
        parameters={"endpoint": "/users", "method": "GET"}
    )
    error2 = tracker.track_error(
        error_type=ErrorType.ENVIRONMENT,
        error_code="RateLimitExceeded",
        message="Rate limit exceeded. Retry after 60 seconds.",
        action=action2,
        context={"api_version": "v1", "user_id": "12345"}
    )
    
    # 恢复尝试2: 等待重试
    recovery_action2 = ActionRecord(
        tool="wait",
        parameters={"duration": 60}
    )
    tracker.track_recovery(
        error_record=error2,
        strategy=RecoveryStrategy.WAIT_RETRY,
        action=recovery_action2,
        success=True,
        notes="Applied exponential backoff strategy"
    )
    
    # 场景3: 参数验证错误
    action3 = ActionRecord(
        tool="calculator",
        parameters={"operation": "divide", "a": 10, "b": 0}
    )
    error3 = tracker.track_error(
        error_type=ErrorType.LOGIC,
        error_code="ZeroDivisionError",
        message="division by zero",
        action=action3,
        context={"calculation_type": "ratio_analysis"}
    )
    
    # 恢复尝试3: 参数验证
    recovery_action3 = ActionRecord(
        tool="validate_params",
        parameters={"operation": "divide", "a": 10, "b": 1}
    )
    tracker.track_recovery(
        error_record=error3,
        strategy=RecoveryStrategy.ALTERNATIVE,
        action=recovery_action3,
        success=True,
        notes="Added parameter validation before calculation"
    )
    
    # 场景4: 语义理解错误
    action4 = ActionRecord(
        tool="text_summarize",
        parameters={"text": "long article...", "max_length": 50}
    )
    error4 = tracker.track_error(
        error_type=ErrorType.SEMANTIC,
        error_code="TaskMismatchError",
        message="Generated detailed analysis instead of brief summary",
        action=action4,
        context={"expected_type": "summary", "actual_type": "analysis"}
    )
    
    # 恢复尝试4: 调整提示
    recovery_action4 = ActionRecord(
        tool="text_summarize",
        parameters={"text": "long article...", "max_length": 50, "style": "bullet_points"}
    )
    tracker.track_recovery(
        error_record=error4,
        strategy=RecoveryStrategy.RETRY,
        action=recovery_action4,
        success=True,
        notes="Enhanced prompt with explicit format requirements"
    )
    
    return tracker


def print_analysis_report(tracker: ErrorTracker):
    """打印分析报告"""
    print("\n" + "="*60)
    print("📊 ERROR PATTERN ANALYSIS REPORT")
    print("="*60)
    
    analysis = tracker.analyze_patterns()
    
    print(f"\n📈 Overview:")
    print(f"   Total Errors: {analysis['total_errors']}")
    print(f"   Resolved Errors: {analysis['resolved_errors']}")
    print(f"   Overall Recovery Rate: {analysis['overall_recovery_rate']:.2%}")
    
    print(f"\n🏷️  Error Type Distribution:")
    for error_type, count in analysis['error_type_distribution'].items():
        percentage = count / analysis['total_errors'] * 100
        print(f"   {error_type.ljust(15)}: {count:2d} ({percentage:5.1f}%)")
    
    print(f"\n🛠️  Tool Error Frequency:")
    for tool, count in list(analysis['tool_error_frequency'].items())[:5]:
        print(f"   {tool.ljust(20)}: {count:2d}")
    
    print(f"\n🎯 Recovery Strategy Effectiveness:")
    for strategy, stats in analysis['recovery_strategy_effectiveness'].items():
        success_rate = stats['success_rate']
        total = stats['total']
        print(f"   {strategy.ljust(15)}: {success_rate:5.1%} ({stats['success']}/{total})")
    
    print(f"\n📅 Recent Error Trends (Last 7 Days):")
    recent_trends = analysis['recent_error_trends']
    for error_pattern, count in list(recent_trends.items())[:5]:
        print(f"   {error_pattern.ljust(25)}: {count:2d}")


def main():
    parser = argparse.ArgumentParser(description="Error Tracker & Failure Learning Demo")
    parser.add_argument("--analyze", action="store_true", help="Run analysis on demo data")
    parser.add_argument("--create-demo", action="store_true", help="Create demo scenarios")
    parser.add_argument("--clear-history", action="store_true", help="Clear error history")
    
    args = parser.parse_args()
    
    if args.clear_history:
        import os
        try:
            os.remove("demo_error_history.json")
            print("🗑️  Error history cleared.")
        except FileNotFoundError:
            print("📁 No error history to clear.")
        return
    
    if args.create_demo:
        tracker = create_demo_scenarios()
        print("\n✅ Demo scenarios created successfully!")
        print_analysis_report(tracker)
        return
    
    if args.analyze:
        tracker = ErrorTracker("demo_error_history.json")
        if not tracker.error_history:
            print("❌ No error history found. Run --create-demo first.")
            return
        print_analysis_report(tracker)
        return
    
    # 默认：创建演示数据并分析
    print("🎯 Error Preservation & Failure Learning Demo")
    print("=" * 50)
    print("\n💡 Manus Philosophy: 'Keep the Wrong Stuff In'")
    print("   Errors are not bugs, they are features.")
    print("   Error recovery is the clearest indicator of true agent behavior.\n")
    
    tracker = create_demo_scenarios()
    print_analysis_report(tracker)
    
    print(f"\n📁 Error history saved to: {tracker.storage_path}")
    print("\n🚀 Try these commands:")
    print("   python error_tracker.py --analyze")
    print("   python error_tracker.py --create-demo")
    print("   python error_tracker.py --clear-history")


if __name__ == "__main__":
    main()
