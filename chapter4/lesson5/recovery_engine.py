#!/usr/bin/env python3
"""
Recovery Engine - 错误恢复机制实现

基于错误历史智能选择和执行恢复策略。
"""

import json
import time
import random
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from error_tracker import ErrorTracker, ErrorRecord, ActionRecord, RecoveryStrategy, ErrorType


class RecoveryPattern(Enum):
    """恢复模式"""
    IMMEDIATE = "immediate"        # 立即重试
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    CIRCUIT_BREAKER = "circuit_breaker"          # 断路器模式
    ALTERNATIVE_PATH = "alternative_path"        # 替代路径
    GRACEFUL_DEGRADATION = "graceful_degradation"  # 优雅降级


@dataclass
class RecoveryContext:
    """恢复上下文"""
    original_error: ErrorRecord
    similar_errors: List[ErrorRecord]
    environment_state: Dict[str, Any]
    retry_count: int = 0
    max_retries: int = 3
    last_attempt_time: Optional[datetime] = None


class RecoveryEngine:
    """智能错误恢复引擎"""
    
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
        self.recovery_strategies = {
            RecoveryStrategy.RETRY: self._execute_retry,
            RecoveryStrategy.WAIT_RETRY: self._execute_wait_retry,
            RecoveryStrategy.ALTERNATIVE: self._execute_alternative,
            RecoveryStrategy.SKIP: self._execute_skip,
            RecoveryStrategy.ABORT: self._execute_abort
        }
        
        # 恢复模式配置
        self.recovery_configs = {
            ErrorType.ENVIRONMENT: {
                "default_strategy": RecoveryStrategy.WAIT_RETRY,
                "max_retries": 3,
                "backoff_multiplier": 2.0,
                "max_wait_time": 300  # 5 minutes
            },
            ErrorType.LOGIC: {
                "default_strategy": RecoveryStrategy.ALTERNATIVE,
                "max_retries": 2,
                "backoff_multiplier": 1.5,
                "max_wait_time": 60
            },
            ErrorType.SEMANTIC: {
                "default_strategy": RecoveryStrategy.RETRY,
                "max_retries": 2,
                "backoff_multiplier": 1.0,
                "max_wait_time": 30
            },
            ErrorType.TIMEOUT: {
                "default_strategy": RecoveryStrategy.WAIT_RETRY,
                "max_retries": 4,
                "backoff_multiplier": 3.0,
                "max_wait_time": 600  # 10 minutes
            },
            ErrorType.PERMISSION: {
                "default_strategy": RecoveryStrategy.ALTERNATIVE,
                "max_retries": 1,
                "backoff_multiplier": 1.0,
                "max_wait_time": 10
            }
        }
        
        print("🔧 Recovery Engine initialized")
    
    def attempt_recovery(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """尝试从错误中恢复"""
        print(f"\n🔄 Starting recovery for error: {error_record.error_code}")
        
        # 构建恢复上下文
        context = self._build_recovery_context(error_record)
        
        # 选择最佳恢复策略
        strategy = self._select_recovery_strategy(context)
        
        print(f"🎯 Selected strategy: {strategy.value}")
        
        # 执行恢复
        result = self._execute_recovery(strategy, context)
        
        # 记录恢复尝试
        recovery_action = ActionRecord(
            tool=f"recovery_{strategy.value}",
            parameters=result.get('action_parameters', {})
        )
        
        self.error_tracker.track_recovery(
            error_record=error_record,
            strategy=strategy,
            action=recovery_action,
            success=result['success'],
            notes=result.get('notes', '')
        )
        
        return result
    
    def _build_recovery_context(self, error_record: ErrorRecord) -> RecoveryContext:
        """构建恢复上下文"""
        similar_errors = self.error_tracker.find_similar_errors(error_record)
        
        # 分析环境状态
        environment_state = {
            "error_frequency": len(similar_errors),
            "recent_failures": len([e for e in similar_errors 
                                  if (datetime.now() - e.timestamp).seconds < 3600]),
            "success_rate": self._calculate_success_rate(similar_errors),
            "current_time": datetime.now(),
            "system_load": random.uniform(0.1, 0.9)  # 模拟系统负载
        }
        
        return RecoveryContext(
            original_error=error_record,
            similar_errors=similar_errors,
            environment_state=environment_state,
            retry_count=len(error_record.recovery_attempts)
        )
    
    def _select_recovery_strategy(self, context: RecoveryContext) -> RecoveryStrategy:
        """智能选择恢复策略"""
        error_type = context.original_error.error_type
        config = self.recovery_configs.get(error_type, self.recovery_configs[ErrorType.ENVIRONMENT])
        
        # 如果重试次数过多，切换策略
        if context.retry_count >= config["max_retries"]:
            return RecoveryStrategy.ABORT
        
        # 根据历史成功率调整策略
        if context.similar_errors:
            successful_strategies = self._analyze_successful_strategies(context.similar_errors)
            if successful_strategies:
                # 选择历史上最成功的策略
                best_strategy = max(successful_strategies.items(), key=lambda x: x[1])[0]
                return RecoveryStrategy(best_strategy)
        
        # 根据环境状态调整策略
        env_state = context.environment_state
        
        # 高频错误使用断路器模式
        if env_state["recent_failures"] > 5:
            return RecoveryStrategy.SKIP
        
        # 系统负载高时使用等待策略
        if env_state["system_load"] > 0.8:
            return RecoveryStrategy.WAIT_RETRY
        
        # 默认策略
        return config["default_strategy"]
    
    def _analyze_successful_strategies(self, similar_errors: List[ErrorRecord]) -> Dict[str, float]:
        """分析成功的恢复策略"""
        strategy_success = {}
        
        for error in similar_errors:
            if error.resolved:
                for attempt in error.recovery_attempts:
                    if attempt['success']:
                        strategy = attempt['strategy']
                        strategy_success[strategy] = strategy_success.get(strategy, 0) + 1
        
        # 计算成功率
        total_attempts = sum(strategy_success.values())
        if total_attempts > 0:
            for strategy in strategy_success:
                strategy_success[strategy] /= total_attempts
        
        return strategy_success
    
    def _calculate_success_rate(self, similar_errors: List[ErrorRecord]) -> float:
        """计算相似错误的成功恢复率"""
        if not similar_errors:
            return 0.0
        
        resolved_count = sum(1 for err in similar_errors if err.resolved)
        return resolved_count / len(similar_errors)
    
    def _execute_recovery(self, strategy: RecoveryStrategy, context: RecoveryContext) -> Dict[str, Any]:
        """执行恢复策略"""
        if strategy in self.recovery_strategies:
            return self.recovery_strategies[strategy](context)
        else:
            return {
                "success": False,
                "message": f"Unknown recovery strategy: {strategy}",
                "action_parameters": {}
            }
    
    def _execute_retry(self, context: RecoveryContext) -> Dict[str, Any]:
        """执行立即重试"""
        print("🔄 Executing immediate retry...")
        
        # 模拟重试逻辑
        success = random.random() > 0.3  # 70% 成功率
        
        return {
            "success": success,
            "message": "Immediate retry completed" if success else "Immediate retry failed",
            "action_parameters": {
                "retry_type": "immediate",
                "attempt_number": context.retry_count + 1
            },
            "notes": f"Retry attempt {context.retry_count + 1}"
        }
    
    def _execute_wait_retry(self, context: RecoveryContext) -> Dict[str, Any]:
        """执行等待重试（指数退避）"""
        error_type = context.original_error.error_type
        config = self.recovery_configs.get(error_type, self.recovery_configs[ErrorType.ENVIRONMENT])
        
        # 计算等待时间（指数退避）
        base_wait = 1  # 1 second
        wait_time = min(
            base_wait * (config["backoff_multiplier"] ** context.retry_count),
            config["max_wait_time"]
        )
        
        print(f"⏳ Waiting {wait_time:.1f} seconds before retry...")
        
        # 模拟等待
        time.sleep(min(wait_time, 2))  # 演示时限制最大等待时间
        
        # 模拟重试成功率（等待后成功率更高）
        success = random.random() > 0.2  # 80% 成功率
        
        return {
            "success": success,
            "message": f"Wait-retry completed after {wait_time:.1f}s" if success else "Wait-retry failed",
            "action_parameters": {
                "retry_type": "wait_retry",
                "wait_time": wait_time,
                "attempt_number": context.retry_count + 1
            },
            "notes": f"Applied exponential backoff: {wait_time:.1f}s wait"
        }
    
    def _execute_alternative(self, context: RecoveryContext) -> Dict[str, Any]:
        """执行替代方案"""
        print("🔀 Executing alternative approach...")
        
        original_action = context.original_error.action
        alternative_tools = self._suggest_alternative_tools(original_action.tool)
        
        if alternative_tools:
            chosen_tool = alternative_tools[0]
            print(f"🛠️  Switching from {original_action.tool} to {chosen_tool}")
            
            # 模拟替代方案成功率
            success = random.random() > 0.25  # 75% 成功率
            
            return {
                "success": success,
                "message": f"Alternative approach using {chosen_tool}" + (" succeeded" if success else " failed"),
                "action_parameters": {
                    "original_tool": original_action.tool,
                    "alternative_tool": chosen_tool,
                    "fallback_reason": context.original_error.error_code
                },
                "notes": f"Switched to alternative tool: {chosen_tool}"
            }
        else:
            return {
                "success": False,
                "message": "No alternative tools available",
                "action_parameters": {"original_tool": original_action.tool},
                "notes": "No viable alternatives found"
            }
    
    def _execute_skip(self, context: RecoveryContext) -> Dict[str, Any]:
        """执行跳过策略"""
        print("⏭️  Skipping problematic operation...")
        
        return {
            "success": True,  # 跳过本身是成功的
            "message": "Operation skipped due to repeated failures",
            "action_parameters": {
                "skipped_tool": context.original_error.action.tool,
                "skip_reason": "circuit_breaker_triggered"
            },
            "notes": f"Circuit breaker activated after {context.retry_count} failures"
        }
    
    def _execute_abort(self, context: RecoveryContext) -> Dict[str, Any]:
        """执行中止策略"""
        print("🛑 Aborting operation after maximum retries...")
        
        return {
            "success": False,
            "message": f"Operation aborted after {context.retry_count} attempts",
            "action_parameters": {
                "aborted_tool": context.original_error.action.tool,
                "total_attempts": context.retry_count,
                "abort_reason": "max_retries_exceeded"
            },
            "notes": f"Maximum retries ({context.retry_count}) exceeded"
        }
    
    def _suggest_alternative_tools(self, original_tool: str) -> List[str]:
        """建议替代工具"""
        alternatives = {
            "file_read": ["file_stream_read", "file_chunk_read", "safe_file_read"],
            "api_call": ["api_call_v2", "graphql_query", "rest_fallback"],
            "database_query": ["cache_lookup", "database_query_readonly", "search_index"],
            "web_scrape": ["api_alternative", "cached_content", "search_results"],
            "calculation": ["calculator_v2", "math_library", "approximation_engine"],
            "text_process": ["text_processor_v2", "nlp_pipeline", "simple_text_ops"]
        }
        
        return alternatives.get(original_tool, [])
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """获取恢复统计信息"""
        analysis = self.error_tracker.analyze_patterns()
        
        # 计算恢复模式统计
        pattern_usage = {pattern.value: 0 for pattern in RecoveryPattern}
        strategy_timings = {}
        
        for error in self.error_tracker.error_history:
            for attempt in error.recovery_attempts:
                strategy = attempt['strategy']
                if strategy not in strategy_timings:
                    strategy_timings[strategy] = []
                
                # 这里可以添加更复杂的时间分析
                strategy_timings[strategy].append(1.0)  # 占位符
        
        return {
            "total_recovery_attempts": sum(len(err.recovery_attempts) 
                                         for err in self.error_tracker.error_history),
            "recovery_success_rate": analysis["overall_recovery_rate"],
            "strategy_effectiveness": analysis["recovery_strategy_effectiveness"],
            "pattern_usage": pattern_usage,
            "average_recovery_time": strategy_timings
        }


def create_recovery_test_scenarios():
    """创建恢复测试场景"""
    tracker = ErrorTracker("recovery_test_history.json")
    engine = RecoveryEngine(tracker)
    
    print("🧪 Creating recovery test scenarios...\n")
    
    # 测试场景列表
    test_scenarios = [
        {
            "name": "File Access Error",
            "error_type": ErrorType.ENVIRONMENT,
            "error_code": "PermissionDenied",
            "message": "Permission denied: '/etc/sensitive_file.conf'",
            "action": ActionRecord(tool="file_read", parameters={"path": "/etc/sensitive_file.conf"})
        },
        {
            "name": "API Rate Limit",
            "error_type": ErrorType.ENVIRONMENT,
            "error_code": "RateLimitExceeded", 
            "message": "Too many requests. Retry after 120 seconds.",
            "action": ActionRecord(tool="api_call", parameters={"endpoint": "/data", "method": "GET"})
        },
        {
            "name": "Database Connection Timeout",
            "error_type": ErrorType.TIMEOUT,
            "error_code": "ConnectionTimeout",
            "message": "Database connection timed out after 30 seconds",
            "action": ActionRecord(tool="database_query", parameters={"query": "SELECT * FROM users"})
        },
        {
            "name": "Invalid Parameter", 
            "error_type": ErrorType.LOGIC,
            "error_code": "ValueError",
            "message": "Invalid value for parameter 'count': -5",
            "action": ActionRecord(tool="data_process", parameters={"count": -5, "operation": "sample"})
        },
        {
            "name": "Resource Exhaustion",
            "error_type": ErrorType.RESOURCE,
            "error_code": "OutOfMemoryError",
            "message": "Insufficient memory to process large dataset",
            "action": ActionRecord(tool="ml_training", parameters={"dataset_size": "10GB", "batch_size": 1000})
        }
    ]
    
    recovery_results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"🔬 Test Scenario {i}: {scenario['name']}")
        print("-" * 50)
        
        # 创建错误记录
        error_record = tracker.track_error(
            error_type=scenario["error_type"],
            error_code=scenario["error_code"],
            message=scenario["message"],
            action=scenario["action"],
            context={"test_scenario": scenario["name"], "scenario_id": i}
        )
        
        # 尝试恢复
        recovery_result = engine.attempt_recovery(error_record)
        recovery_results.append({
            "scenario": scenario["name"],
            "original_error": scenario["error_code"],
            "recovery_success": recovery_result["success"],
            "recovery_message": recovery_result["message"]
        })
        
        print(f"Result: {'✅ SUCCESS' if recovery_result['success'] else '❌ FAILED'}")
        print(f"Message: {recovery_result['message']}\n")
    
    return tracker, engine, recovery_results


def print_recovery_report(engine: RecoveryEngine, results: List[Dict]):
    """打印恢复报告"""
    print("\n" + "="*60)
    print("🔧 RECOVERY ENGINE TEST REPORT")
    print("="*60)
    
    # 测试结果总结
    total_tests = len(results)
    successful_recoveries = sum(1 for r in results if r["recovery_success"])
    success_rate = successful_recoveries / total_tests if total_tests > 0 else 0
    
    print(f"\n📊 Test Summary:")
    print(f"   Total Test Scenarios: {total_tests}")
    print(f"   Successful Recoveries: {successful_recoveries}")
    print(f"   Recovery Success Rate: {success_rate:.1%}")
    
    print(f"\n📋 Individual Results:")
    for result in results:
        status = "✅" if result["recovery_success"] else "❌"
        print(f"   {status} {result['scenario'].ljust(25)}: {result['recovery_message']}")
    
    # 引擎统计
    stats = engine.get_recovery_statistics()
    print(f"\n🔧 Engine Statistics:")
    print(f"   Total Recovery Attempts: {stats['total_recovery_attempts']}")
    print(f"   Overall Success Rate: {stats['recovery_success_rate']:.1%}")
    
    print(f"\n🎯 Strategy Effectiveness:")
    for strategy, effectiveness in stats['strategy_effectiveness'].items():
        if effectiveness['total'] > 0:
            rate = effectiveness['success_rate']
            total = effectiveness['total']
            success = effectiveness['success']
            print(f"   {strategy.ljust(15)}: {rate:5.1%} ({success}/{total})")


def main():
    parser = argparse.ArgumentParser(description="Recovery Engine Demo")
    parser.add_argument("--test-scenarios", action="store_true", help="Run recovery test scenarios")
    parser.add_argument("--analyze", action="store_true", help="Analyze existing recovery data")
    parser.add_argument("--clear-history", action="store_true", help="Clear recovery test history")
    
    args = parser.parse_args()
    
    if args.clear_history:
        import os
        try:
            os.remove("recovery_test_history.json")
            print("🗑️  Recovery test history cleared.")
        except FileNotFoundError:
            print("📁 No recovery test history to clear.")
        return
    
    if args.analyze:
        tracker = ErrorTracker("recovery_test_history.json")
        if not tracker.error_history:
            print("❌ No recovery history found. Run --test-scenarios first.")
            return
        
        engine = RecoveryEngine(tracker)
        stats = engine.get_recovery_statistics()
        
        print("📊 Recovery Engine Analysis")
        print("=" * 40)
        print(f"Total Recovery Attempts: {stats['total_recovery_attempts']}")
        print(f"Overall Success Rate: {stats['recovery_success_rate']:.1%}")
        return
    
    if args.test_scenarios:
        tracker, engine, results = create_recovery_test_scenarios()
        print_recovery_report(engine, results)
        print(f"\n📁 Recovery history saved to: {tracker.storage_path}")
        return
    
    # 默认：运行完整演示
    print("🔧 Recovery Engine Demo")
    print("=" * 30)
    print("\n💡 Intelligent Error Recovery System")
    print("   - Learns from error patterns")
    print("   - Adapts recovery strategies") 
    print("   - Maximizes success rates\n")
    
    tracker, engine, results = create_recovery_test_scenarios()
    print_recovery_report(engine, results)
    
    print(f"\n📁 Data saved to: {tracker.storage_path}")
    print("\n🚀 Try these commands:")
    print("   python recovery_engine.py --test-scenarios")
    print("   python recovery_engine.py --analyze")
    print("   python recovery_engine.py --clear-history")


if __name__ == "__main__":
    main()
