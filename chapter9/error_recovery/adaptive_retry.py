#!/usr/bin/env python3
"""
Adaptive Retry - 自适应重试策略

基于历史错误模式动态调整重试策略，实现智能的失败恢复。
"""

import time
import random
import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Dict, List, Any, Optional, Callable
from dataclasses import asdict, dataclass, field, replace
from enum import Enum
import math

from error_tracker import ErrorTracker, ErrorRecord, ActionRecord, ErrorType


class RetryPattern(Enum):
    """重试模式"""
    FIXED_INTERVAL = "fixed_interval"          # 固定间隔
    LINEAR_BACKOFF = "linear_backoff"          # 线性退避
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    FIBONACCI_BACKOFF = "fibonacci_backoff"    # 斐波那契退避
    JITTERED_EXPONENTIAL = "jittered_exponential"  # 带抖动的指数退避
    ADAPTIVE_LEARNING = "adaptive_learning"    # 自适应学习


@dataclass
class RetryConfig:
    """重试配置"""
    pattern: RetryPattern
    base_delay: float = 1.0
    max_delay: float = 60.0
    max_attempts: int = 5
    backoff_multiplier: float = 2.0
    jitter_factor: float = 0.1
    timeout: float = 300.0
    
    # 自适应参数
    success_rate_threshold: float = 0.7
    learning_rate: float = 0.1
    adaptation_window: int = 10


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt_number: int
    delay_used: float
    success: bool
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: Optional[float] = None
    planned_delay: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class RetrySession:
    """重试会话"""
    session_id: str
    operation_type: str
    original_action: ActionRecord
    config: RetryConfig
    attempts: List[RetryAttempt] = field(default_factory=list)
    final_success: bool = False
    total_duration: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class AdaptiveRetry:
    """自适应重试系统"""
    
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
        self.retry_sessions: List[RetrySession] = []
        self.learned_configs: Dict[str, RetryConfig] = {}
        self.history_path = Path(error_tracker.storage_path).with_suffix(".retries.json")
        
        # 默认配置
        self.default_configs = {
            ErrorType.ENVIRONMENT: RetryConfig(
                pattern=RetryPattern.EXPONENTIAL_BACKOFF,
                base_delay=1.0,
                max_delay=60.0,
                max_attempts=5,
                backoff_multiplier=2.0
            ),
            ErrorType.LOGIC: RetryConfig(
                pattern=RetryPattern.LINEAR_BACKOFF,
                base_delay=0.5,
                max_delay=10.0,
                max_attempts=3,
                backoff_multiplier=1.5
            ),
            ErrorType.TIMEOUT: RetryConfig(
                pattern=RetryPattern.JITTERED_EXPONENTIAL,
                base_delay=2.0,
                max_delay=120.0,
                max_attempts=4,
                backoff_multiplier=3.0,
                jitter_factor=0.2
            ),
            ErrorType.SEMANTIC: RetryConfig(
                pattern=RetryPattern.FIXED_INTERVAL,
                base_delay=1.0,
                max_delay=5.0,
                max_attempts=2,
                backoff_multiplier=1.0
            )
        }

        self._load_history()
        
        print("🔄 Adaptive Retry system initialized")
    
    def retry_operation(self, 
                       action: ActionRecord,
                       operation_func: Callable,
                       error_type: ErrorType = None) -> Dict[str, Any]:
        """执行带有自适应重试的操作"""
        session_id = f"retry_{int(time.time())}_{random.randint(1000, 9999)}"
        operation_type = f"{action.tool}:{error_type.value if error_type else 'unknown'}"
        
        # 获取适应性配置
        config = replace(self._get_adaptive_config(operation_type, error_type))
        
        session = RetrySession(
            session_id=session_id,
            operation_type=operation_type,
            original_action=action,
            config=config
        )
        
        print(f"🚀 Starting retry session: {session_id}")
        print(f"   Operation: {operation_type}")
        print(f"   Pattern: {config.pattern.value}")
        print(f"   Max attempts: {config.max_attempts}")
        
        start_time = time.time()
        last_error = None
        
        for attempt_num in range(1, config.max_attempts + 1):
            print(f"\n🔄 Attempt {attempt_num}/{config.max_attempts}")
            
            # 计算延迟时间
            if attempt_num > 1:  # 第一次尝试不需要延迟
                planned_delay = self._calculate_delay(config, attempt_num - 1)
                delay = min(planned_delay, 2.0)
                print(f"⏳ 演示等待 {delay:.2f}s，策略计算的等待为 {planned_delay:.2f}s。")
                time.sleep(delay)
            else:
                delay = 0.0
                planned_delay = 0.0
            
            # 执行操作
            attempt_start = time.time()
            try:
                result = operation_func()
                response_time = time.time() - attempt_start
                
                # 记录成功尝试
                attempt = RetryAttempt(
                    attempt_number=attempt_num,
                    delay_used=delay,
                    planned_delay=planned_delay,
                    success=True,
                    response_time=response_time
                )
                session.attempts.append(attempt)
                session.final_success = True
                
                print(f"✅ Operation succeeded on attempt {attempt_num}")
                print(f"   Response time: {response_time:.2f}s")
                break
                
            except Exception as e:
                response_time = time.time() - attempt_start
                error_code = type(e).__name__
                last_error = str(e)
                
                # 记录失败尝试
                attempt = RetryAttempt(
                    attempt_number=attempt_num,
                    delay_used=delay,
                    planned_delay=planned_delay,
                    success=False,
                    error_code=error_code,
                    error_message=str(e),
                    response_time=response_time
                )
                session.attempts.append(attempt)
                
                print(f"❌ Attempt {attempt_num} failed: {error_code}")
                
                if attempt_num == config.max_attempts:
                    print(f"🛑 All retry attempts exhausted")
        
        session.total_duration = time.time() - start_time
        self.retry_sessions.append(session)
        
        # 更新学习配置
        self._update_learned_config(session)
        self._save_history()
        
        return {
            "session_id": session_id,
            "success": session.final_success,
            "attempts_used": len(session.attempts),
            "total_duration": session.total_duration,
            "last_error": last_error if not session.final_success else None
        }

    def _load_history(self):
        if not self.history_path.exists():
            return
        data = json.loads(self.history_path.read_text(encoding="utf-8"))
        for item in data.get("retry_sessions", []):
            session = dict(item)
            action = dict(session["original_action"])
            action["timestamp"] = datetime.fromisoformat(action["timestamp"])
            session["original_action"] = ActionRecord(**action)
            config = dict(session["config"])
            config["pattern"] = RetryPattern(config["pattern"])
            session["config"] = RetryConfig(**config)
            attempts = []
            for item in session["attempts"]:
                attempt = dict(item)
                attempt["timestamp"] = datetime.fromisoformat(attempt["timestamp"])
                attempts.append(RetryAttempt(**attempt))
            session["attempts"] = attempts
            session["created_at"] = datetime.fromisoformat(session["created_at"])
            self.retry_sessions.append(RetrySession(**session))
        for key, item in data.get("learned_configs", {}).items():
            config = dict(item)
            config["pattern"] = RetryPattern(config["pattern"])
            self.learned_configs[key] = RetryConfig(**config)
        print(f"📚 已加载 {len(self.retry_sessions)} 次重试会话，来源 {self.history_path}。")

    def _save_history(self):
        def encode(value):
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, Enum):
                return value.value
            raise TypeError(f"Unsupported history value: {type(value).__name__}")

        data = {
            "retry_sessions": [asdict(session) for session in self.retry_sessions],
            "learned_configs": {key: asdict(config) for key, config in self.learned_configs.items()},
        }
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        handle = NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.history_path.parent,
                                    delete=False)
        temp_path = Path(handle.name)
        try:
            with handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, default=encode)
            os.replace(temp_path, self.history_path)
        finally:
            temp_path.unlink(missing_ok=True)
    
    def _get_adaptive_config(self, operation_type: str, error_type: ErrorType) -> RetryConfig:
        """获取自适应配置"""
        # 检查是否有已学习的配置
        if operation_type in self.learned_configs:
            learned_config = self.learned_configs[operation_type]
            print(f"📚 Using learned config for {operation_type}")
            return learned_config
        
        # 使用默认配置
        default_config = self.default_configs.get(error_type, self.default_configs[ErrorType.ENVIRONMENT])
        print(f"🔧 Using default config for {error_type.value if error_type else 'unknown'}")
        return default_config
    
    def _calculate_delay(self, config: RetryConfig, attempt_number: int) -> float:
        """根据配置计算延迟时间"""
        if config.pattern == RetryPattern.FIXED_INTERVAL:
            return config.base_delay
        
        elif config.pattern == RetryPattern.LINEAR_BACKOFF:
            delay = config.base_delay * attempt_number
        
        elif config.pattern == RetryPattern.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt_number - 1))
        
        elif config.pattern == RetryPattern.FIBONACCI_BACKOFF:
            delay = config.base_delay * self._fibonacci(attempt_number)
        
        elif config.pattern == RetryPattern.JITTERED_EXPONENTIAL:
            base_delay = config.base_delay * (config.backoff_multiplier ** (attempt_number - 1))
            jitter = base_delay * config.jitter_factor * (random.random() - 0.5) * 2
            delay = base_delay + jitter
        
        else:  # ADAPTIVE_LEARNING 或其他
            delay = config.base_delay * (config.backoff_multiplier ** (attempt_number - 1))
        
        return min(delay, config.max_delay)
    
    def _fibonacci(self, n: int) -> int:
        """计算斐波那契数列"""
        if n <= 1:
            return 1
        elif n == 2:
            return 2
        
        a, b = 1, 2
        for _ in range(3, n + 1):
            a, b = b, a + b
        return b
    
    def _update_learned_config(self, session: RetrySession):
        """基于会话结果更新学习配置"""
        operation_type = session.operation_type
        
        # 计算会话的成功率和效率
        success_rate = 1.0 if session.final_success else 0.0
        efficiency = 1.0 / len(session.attempts) if session.attempts else 0.0
        
        # 如果还没有学习配置，创建一个
        if operation_type not in self.learned_configs:
            self.learned_configs[operation_type] = RetryConfig(**session.config.__dict__)
        
        learned_config = self.learned_configs[operation_type]
        
        # 根据结果调整配置
        if session.final_success:
            # 成功了，可以稍微降低重试次数或延迟
            if len(session.attempts) == 1:
                # 第一次就成功，可能不需要那么多重试
                learned_config.max_attempts = max(1, learned_config.max_attempts - 1)
            else:
                # 多次尝试后成功，当前配置还行
                pass
        else:
            # 失败了，需要增加重试次数或调整策略
            learned_config.max_attempts = min(10, learned_config.max_attempts + 1)
            
            # 如果是超时问题，增加延迟
            timeout_errors = [a for a in session.attempts if a.error_code and 'timeout' in a.error_code.lower()]
            if timeout_errors:
                learned_config.base_delay = min(10.0, learned_config.base_delay * 1.2)
        
        print(f"📈 Updated learned config for {operation_type}")
        print(f"   Max attempts: {learned_config.max_attempts}")
        print(f"   Base delay: {learned_config.base_delay:.2f}s")
    
    def analyze_retry_patterns(self) -> Dict[str, Any]:
        """分析重试模式"""
        if not self.retry_sessions:
            return {"message": "No retry sessions to analyze"}
        
        # 基本统计
        total_sessions = len(self.retry_sessions)
        successful_sessions = sum(1 for s in self.retry_sessions if s.final_success)
        success_rate = successful_sessions / total_sessions
        
        # 尝试次数统计
        attempt_counts = [len(s.attempts) for s in self.retry_sessions]
        avg_attempts = sum(attempt_counts) / len(attempt_counts)
        
        # 持续时间统计
        durations = [s.total_duration for s in self.retry_sessions]
        avg_duration = sum(durations) / len(durations)
        
        # 按操作类型分析
        type_stats = {}
        for session in self.retry_sessions:
            op_type = session.operation_type
            if op_type not in type_stats:
                type_stats[op_type] = {
                    'total': 0,
                    'successful': 0,
                    'total_attempts': 0,
                    'total_duration': 0.0
                }
            
            stats = type_stats[op_type]
            stats['total'] += 1
            if session.final_success:
                stats['successful'] += 1
            stats['total_attempts'] += len(session.attempts)
            stats['total_duration'] += session.total_duration
        
        # 计算每种类型的成功率
        for op_type, stats in type_stats.items():
            stats['success_rate'] = stats['successful'] / stats['total']
            stats['avg_attempts'] = stats['total_attempts'] / stats['total']
            stats['avg_duration'] = stats['total_duration'] / stats['total']
        
        # 重试模式效果分析
        pattern_stats = {}
        for session in self.retry_sessions:
            pattern = session.config.pattern.value
            if pattern not in pattern_stats:
                pattern_stats[pattern] = {'total': 0, 'successful': 0}
            
            pattern_stats[pattern]['total'] += 1
            if session.final_success:
                pattern_stats[pattern]['successful'] += 1
        
        for pattern, stats in pattern_stats.items():
            stats['success_rate'] = stats['successful'] / stats['total']
        
        return {
            'total_sessions': total_sessions,
            'overall_success_rate': success_rate,
            'average_attempts': avg_attempts,
            'average_duration': avg_duration,
            'operation_type_stats': type_stats,
            'retry_pattern_effectiveness': pattern_stats,
            'learned_configs_count': len(self.learned_configs)
        }
    
    def get_recommendations(self) -> List[str]:
        """获取优化建议"""
        analysis = self.analyze_retry_patterns()
        recommendations = []
        
        if analysis.get('total_sessions', 0) == 0:
            return ["No retry data available for analysis"]
        
        # 基于整体成功率的建议
        overall_success = analysis.get('overall_success_rate', 0)
        if overall_success < 0.5:
            recommendations.append("🔧 Overall retry success rate is low. Consider reviewing error handling strategies.")
        elif overall_success > 0.9:
            recommendations.append("✅ Excellent retry success rate. Current strategies are working well.")
        
        # 基于平均尝试次数的建议
        avg_attempts = analysis.get('average_attempts', 0)
        if avg_attempts > 4:
            recommendations.append("⚡ High average attempts detected. Consider optimizing retry delays or error prevention.")
        elif avg_attempts < 2:
            recommendations.append("🚀 Low retry usage suggests good operation reliability or potentially insufficient retry attempts.")
        
        # 基于操作类型的建议
        type_stats = analysis.get('operation_type_stats', {})
        for op_type, stats in type_stats.items():
            if stats['success_rate'] < 0.3:
                recommendations.append(f"❌ Operation '{op_type}' has very low success rate ({stats['success_rate']:.1%}). Review operation logic.")
            elif stats['avg_attempts'] > 5:
                recommendations.append(f"🔄 Operation '{op_type}' requires too many retries on average. Consider alternative approaches.")
        
        # 基于重试模式的建议
        pattern_stats = analysis.get('retry_pattern_effectiveness', {})
        best_pattern = max(pattern_stats.items(), key=lambda x: x[1]['success_rate'], default=(None, None))
        if best_pattern[0]:
            recommendations.append(f"🎯 '{best_pattern[0]}' pattern shows best results ({best_pattern[1]['success_rate']:.1%} success rate).")
        
        return recommendations if recommendations else ["📊 Not enough data for specific recommendations yet."]


def create_demo_operations():
    """创建演示操作函数"""
    
    def unstable_file_operation():
        """模拟不稳定的文件操作"""
        if random.random() < 0.3:  # 30% 成功率
            return {"status": "success", "data": "file_content"}
        else:
            raise FileNotFoundError("Simulated file not found")
    
    def rate_limited_api():
        """模拟有限速的API"""
        if random.random() < 0.4:  # 40% 成功率
            return {"status": "success", "data": "api_response"}
        else:
            raise ConnectionError("Rate limit exceeded")
    
    def timeout_prone_service():
        """模拟容易超时的服务"""
        if random.random() < 0.5:  # 50% 成功率
            return {"status": "success", "data": "service_response"}
        else:
            raise TimeoutError("Service timeout")
    
    def parameter_sensitive_operation():
        """模拟对参数敏感的操作"""
        if random.random() < 0.6:  # 60% 成功率
            return {"status": "success", "data": "operation_result"}
        else:
            raise ValueError("Invalid parameter value")
    
    return {
        "file_operation": unstable_file_operation,
        "api_call": rate_limited_api,
        "service_request": timeout_prone_service,
        "data_processing": parameter_sensitive_operation
    }


def run_retry_demo():
    """运行重试演示"""
    print("🔄 Adaptive Retry System Demo")
    print("=" * 40)
    
    # 创建错误跟踪器和重试系统
    tracker = ErrorTracker("adaptive_retry_history.json")
    retry_system = AdaptiveRetry(tracker)
    
    # 获取演示操作
    demo_operations = create_demo_operations()
    
    test_scenarios = [
        ("file_read", "file_operation", ErrorType.ENVIRONMENT),
        ("api_call", "api_call", ErrorType.ENVIRONMENT), 
        ("web_request", "service_request", ErrorType.TIMEOUT),
        ("data_validate", "data_processing", ErrorType.LOGIC),
        ("api_call", "api_call", ErrorType.ENVIRONMENT),  # 重复测试学习效果
        ("file_read", "file_operation", ErrorType.ENVIRONMENT),  # 重复测试学习效果
    ]
    
    results = []
    
    print(f"\n🧪 Running {len(test_scenarios)} test scenarios...\n")
    
    for i, (tool_name, operation_key, error_type) in enumerate(test_scenarios, 1):
        print(f"{'='*50}")
        print(f"🔬 Test Scenario {i}: {tool_name} ({error_type.value})")
        print(f"{'='*50}")
        
        action = ActionRecord(
            tool=tool_name,
            parameters={"test_param": f"value_{i}"}
        )
        
        operation_func = demo_operations[operation_key]
        
        result = retry_system.retry_operation(
            action=action,
            operation_func=operation_func,
            error_type=error_type
        )
        
        results.append({
            "scenario": f"{tool_name}:{error_type.value}",
            "success": result["success"],
            "attempts": result["attempts_used"],
            "duration": result["total_duration"]
        })
        
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"\n{status} - {result['attempts_used']} attempts, {result['total_duration']:.2f}s total")
        
        if not result["success"]:
            print(f"Final error: {result['last_error']}")
    
    return retry_system, results


def print_retry_analysis(retry_system: AdaptiveRetry, results: List[Dict]):
    """打印重试分析报告"""
    print("\n" + "="*60)
    print("📊 ADAPTIVE RETRY ANALYSIS REPORT")
    print("="*60)
    
    # 测试结果总结
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    print(f"\n🎯 Test Results Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success Rate: {success_rate:.1%}")
    
    # 详细分析
    analysis = retry_system.analyze_retry_patterns()
    
    print(f"\n📈 Retry System Analysis:")
    print(f"   Total Sessions: {analysis['total_sessions']}")
    print(f"   Overall Success Rate: {analysis['overall_success_rate']:.1%}")
    print(f"   Average Attempts: {analysis['average_attempts']:.1f}")
    print(f"   Average Duration: {analysis['average_duration']:.2f}s")
    print(f"   Learned Configs: {analysis['learned_configs_count']}")
    
    # 操作类型统计
    print(f"\n🔧 Operation Type Performance:")
    for op_type, stats in analysis['operation_type_stats'].items():
        print(f"   {op_type}:")
        print(f"      Success Rate: {stats['success_rate']:.1%}")
        print(f"      Avg Attempts: {stats['avg_attempts']:.1f}")
        print(f"      Avg Duration: {stats['avg_duration']:.2f}s")
    
    # 重试模式效果
    print(f"\n🎯 Retry Pattern Effectiveness:")
    for pattern, stats in analysis['retry_pattern_effectiveness'].items():
        success_rate = stats['success_rate']
        total = stats['total']
        print(f"   {pattern.ljust(20)}: {success_rate:5.1%} ({stats['successful']}/{total})")
    
    # 建议
    recommendations = retry_system.get_recommendations()
    print(f"\n💡 Optimization Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")


def run_retry_benchmark():
    """用固定故障验证预算调整、配置快照、等待与持久化读回。"""
    with TemporaryDirectory() as directory:
        history = str(Path(directory) / "benchmark.json")
        retry_system = AdaptiveRetry(ErrorTracker(history))
        retry_system.default_configs[ErrorType.ENVIRONMENT] = RetryConfig(
            RetryPattern.EXPONENTIAL_BACKOFF, base_delay=0, max_attempts=2
        )
        calls = 0

        def fails_twice():
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise ConnectionError("固定教学故障")
            return "已恢复"

        action = ActionRecord("fixed_service", {"failures_before_success": 2})
        first = retry_system.retry_operation(action, fails_twice, ErrorType.ENVIRONMENT)
        calls = 0
        second = retry_system.retry_operation(action, fails_twice, ErrorType.ENVIRONMENT)
        retry_system.default_configs[ErrorType.SEMANTIC] = RetryConfig(
            RetryPattern.FIXED_INTERVAL, base_delay=3, max_attempts=2
        )
        calls = 1
        retry_system.retry_operation(ActionRecord("delay_probe", {}), fails_twice, ErrorType.SEMANTIC)
        loaded = AdaptiveRetry(ErrorTracker(history))
        for session in loaded.retry_sessions:
            print(f"会话 {session.operation_type}：预算 {session.config.max_attempts}，"
                  f"实际尝试 {len(session.attempts)}，恢复 {session.final_success}")
            print(f"  等待记录 {[(attempt.planned_delay, attempt.delay_used) for attempt in session.attempts]}")
        checks = {
            "预算两次时固定故障尚未恢复": not first["success"] and first["attempts_used"] == 2,
            "沿用学到的三次预算后恢复": second["success"] and second["attempts_used"] == 3,
            "旧会话保留原预算快照": loaded.retry_sessions[0].config.max_attempts == 2,
            "重建对象读回三次会话和配置": len(loaded.retry_sessions) == 3
                and loaded.learned_configs["fixed_service:environment"].max_attempts == 3,
            "策略等待与演示等待分别记录": loaded.retry_sessions[2].attempts[1].planned_delay == 3
                and loaded.retry_sessions[2].attempts[1].delay_used == 2,
        }
    for description, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {description}")
    return all(checks.values())


def main():
    parser = argparse.ArgumentParser(description="Adaptive Retry System Demo")
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    parser.add_argument("--analyze", action="store_true", help="Analyze existing retry data")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark test")
    
    args = parser.parse_args()
    
    if args.analyze:
        tracker = ErrorTracker("adaptive_retry_history.json")
        retry_system = AdaptiveRetry(tracker)
        
        if not retry_system.retry_sessions:
            raise SystemExit("未找到重试会话。请在同一目录先运行 --demo。")
        
        analysis = retry_system.analyze_retry_patterns()
        recommendations = retry_system.get_recommendations()
        
        print("📊 Adaptive Retry Analysis")
        print("=" * 30)
        for key, value in analysis.items():
            if key not in ['operation_type_stats', 'retry_pattern_effectiveness']:
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")
        return
    
    if args.benchmark:
        if not run_retry_benchmark():
            raise SystemExit(1)
        return
    
    if args.demo or not any(vars(args).values()):
        # 默认运行演示
        print("🔄 Adaptive Retry System")
        print("=" * 30)
        print("\n💡 Key Features:")
        print("   • Learns from retry patterns")
        print("   • Adapts strategies dynamically")
        print("   • Optimizes success rates")
        print("   • Minimizes resource usage\n")
        
        retry_system, results = run_retry_demo()
        print_retry_analysis(retry_system, results)
        
        print("\n🚀 Try these commands:")
        print("   python adaptive_retry.py --demo")
        print("   python adaptive_retry.py --analyze")
        print("   python adaptive_retry.py --benchmark")
        return
    
    # 显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
