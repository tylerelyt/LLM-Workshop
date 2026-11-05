#!/usr/bin/env python3
"""
Failure Learner - 从失败中学习的核心逻辑

实现智能的失败学习机制，让Agent从错误中获得洞察并改进行为。
"""

import json
import math
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np

from error_tracker import ErrorTracker, ErrorRecord, ActionRecord, ErrorType


@dataclass 
class LearningInsight:
    """学习洞察"""
    insight_type: str
    description: str
    confidence: float
    supporting_evidence: List[str]
    actionable_advice: str
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class BehaviorPattern:
    """行为模式"""
    pattern_id: str
    pattern_type: str  # success, failure, mixed
    trigger_conditions: Dict[str, Any]
    observed_outcomes: List[str]
    frequency: int
    last_observed: datetime
    confidence_score: float


class FailureLearner:
    """失败学习器 - 从错误中提取洞察和模式"""
    
    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker
        self.learned_insights: List[LearningInsight] = []
        self.behavior_patterns: Dict[str, BehaviorPattern] = {}
        self.knowledge_base = self._initialize_knowledge_base()
        
        print("🧠 Failure Learner initialized")
    
    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """初始化知识库"""
        return {
            "error_prevention_rules": [
                "Always validate parameters before API calls",
                "Check file existence before read operations", 
                "Implement exponential backoff for rate-limited APIs",
                "Use circuit breakers for frequently failing operations",
                "Validate input ranges for mathematical operations"
            ],
            "recovery_strategies": {
                "file_operations": ["check_permissions", "try_alternative_path", "create_directory"],
                "api_calls": ["retry_with_backoff", "use_cached_data", "fallback_endpoint"],
                "calculations": ["validate_inputs", "use_safe_defaults", "approximate_result"],
                "network": ["check_connectivity", "use_offline_mode", "retry_different_endpoint"]
            },
            "success_indicators": [
                "operation_completed_without_error",
                "result_within_expected_range", 
                "response_time_acceptable",
                "resource_usage_normal"
            ]
        }
    
    def analyze_failure_patterns(self) -> List[LearningInsight]:
        """分析失败模式并生成学习洞察"""
        print("🔍 Analyzing failure patterns...")
        
        insights = []
        
        # 1. 分析频繁失败的操作
        insights.extend(self._analyze_frequent_failures())
        
        # 2. 分析时间相关的失败模式
        insights.extend(self._analyze_temporal_patterns())
        
        # 3. 分析参数相关的失败模式
        insights.extend(self._analyze_parameter_patterns())
        
        # 4. 分析恢复策略的有效性
        insights.extend(self._analyze_recovery_effectiveness())
        
        # 5. 分析错误传播链
        insights.extend(self._analyze_error_chains())
        
        self.learned_insights.extend(insights)
        return insights
    
    def _analyze_frequent_failures(self) -> List[LearningInsight]:
        """分析频繁失败的操作"""
        insights = []
        
        # 统计每种工具的失败次数
        tool_failures = defaultdict(int)
        tool_errors = defaultdict(list)
        
        for error in self.error_tracker.error_history:
            tool = error.action.tool
            tool_failures[tool] += 1
            tool_errors[tool].append(error)
        
        # 识别高失败率的工具
        total_errors = len(self.error_tracker.error_history)
        for tool, failure_count in tool_failures.items():
            failure_rate = failure_count / total_errors
            
            if failure_rate > 0.3 and failure_count >= 3:  # 30%以上失败率且至少3次失败
                # 分析失败原因
                error_codes = Counter(err.error_code for err in tool_errors[tool])
                most_common_error = error_codes.most_common(1)[0]
                
                insight = LearningInsight(
                    insight_type="frequent_failure",
                    description=f"Tool '{tool}' has high failure rate ({failure_rate:.1%})",
                    confidence=min(0.9, failure_rate * 2),  # 基于失败率计算置信度
                    supporting_evidence=[
                        f"Failed {failure_count} out of {total_errors} total operations",
                        f"Most common error: {most_common_error[0]} ({most_common_error[1]} times)",
                        f"Error types: {list(error_codes.keys())}"
                    ],
                    actionable_advice=f"Consider implementing pre-validation for {tool} operations or using alternative tools"
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_temporal_patterns(self) -> List[LearningInsight]:
        """分析时间相关的失败模式"""
        insights = []
        
        if len(self.error_tracker.error_history) < 5:
            return insights
        
        # 分析错误发生的时间间隔
        timestamps = [err.timestamp for err in self.error_tracker.error_history]
        timestamps.sort()
        
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        if intervals:
            avg_interval = np.mean(intervals)
            std_interval = np.std(intervals)
            
            # 检测错误爆发模式（短时间内多次错误）
            burst_threshold = avg_interval - std_interval
            burst_errors = sum(1 for interval in intervals if interval < burst_threshold)
            
            if burst_errors > len(intervals) * 0.3:  # 30%以上是突发错误
                insight = LearningInsight(
                    insight_type="temporal_burst",
                    description="Detected error burst pattern - multiple failures in short time windows",
                    confidence=0.8,
                    supporting_evidence=[
                        f"Average error interval: {avg_interval:.1f} seconds",
                        f"Burst errors detected: {burst_errors}/{len(intervals)}",
                        f"Burst threshold: {burst_threshold:.1f} seconds"
                    ],
                    actionable_advice="Implement circuit breaker pattern to prevent cascading failures"
                )
                insights.append(insight)
        
        return insights
    
    def _analyze_parameter_patterns(self) -> List[LearningInsight]:
        """分析参数相关的失败模式"""
        insights = []
        
        # 分析导致错误的参数模式
        parameter_failures = defaultdict(list)
        
        for error in self.error_tracker.error_history:
            tool = error.action.tool
            params = error.action.parameters
            
            for param_name, param_value in params.items():
                key = f"{tool}.{param_name}"
                parameter_failures[key].append({
                    'value': param_value,
                    'error_code': error.error_code,
                    'error_type': error.error_type.value
                })
        
        # 识别问题参数
        for param_key, failures in parameter_failures.items():
            if len(failures) >= 3:  # 至少3次失败
                values = [f['value'] for f in failures]
                error_codes = [f['error_code'] for f in failures]
                
                # 检测特定值模式
                value_counter = Counter(str(v) for v in values)
                most_common_value = value_counter.most_common(1)[0]
                
                if most_common_value[1] >= 2:  # 同一值导致多次失败
                    insight = LearningInsight(
                        insight_type="problematic_parameter",
                        description=f"Parameter '{param_key}' frequently causes failures",
                        confidence=0.7,
                        supporting_evidence=[
                            f"Failed {len(failures)} times",
                            f"Problematic value: '{most_common_value[0]}' ({most_common_value[1]} times)",
                            f"Error codes: {list(set(error_codes))}"
                        ],
                        actionable_advice=f"Add validation for parameter '{param_key}' before use"
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_recovery_effectiveness(self) -> List[LearningInsight]:
        """分析恢复策略的有效性"""
        insights = []
        
        # 统计恢复策略的成功率
        strategy_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        
        for error in self.error_tracker.error_history:
            for attempt in error.recovery_attempts:
                strategy = attempt['strategy']
                strategy_stats[strategy]['total'] += 1
                if attempt['success']:
                    strategy_stats[strategy]['success'] += 1
        
        # 识别低效的恢复策略
        for strategy, stats in strategy_stats.items():
            if stats['total'] >= 3:  # 至少使用3次
                success_rate = stats['success'] / stats['total']
                
                if success_rate < 0.3:  # 成功率低于30%
                    insight = LearningInsight(
                        insight_type="ineffective_recovery",
                        description=f"Recovery strategy '{strategy}' has low success rate",
                        confidence=0.8,
                        supporting_evidence=[
                            f"Success rate: {success_rate:.1%}",
                            f"Successful attempts: {stats['success']}/{stats['total']}"
                        ],
                        actionable_advice=f"Consider alternative recovery strategies for '{strategy}' scenarios"
                    )
                    insights.append(insight)
                
                elif success_rate > 0.8:  # 成功率高于80%
                    insight = LearningInsight(
                        insight_type="effective_recovery",
                        description=f"Recovery strategy '{strategy}' is highly effective",
                        confidence=0.9,
                        supporting_evidence=[
                            f"Success rate: {success_rate:.1%}",
                            f"Successful attempts: {stats['success']}/{stats['total']}"
                        ],
                        actionable_advice=f"Prioritize '{strategy}' strategy for similar error types"
                    )
                    insights.append(insight)
        
        return insights
    
    def _analyze_error_chains(self) -> List[LearningInsight]:
        """分析错误传播链"""
        insights = []
        
        # 按时间排序错误
        sorted_errors = sorted(self.error_tracker.error_history, key=lambda x: x.timestamp)
        
        # 检测错误链（短时间内连续发生的相关错误）
        chain_threshold = timedelta(minutes=5)  # 5分钟内的错误认为是相关的
        error_chains = []
        current_chain = []
        
        for i, error in enumerate(sorted_errors):
            if not current_chain:
                current_chain = [error]
            else:
                last_error = current_chain[-1]
                time_diff = error.timestamp - last_error.timestamp
                
                if time_diff <= chain_threshold:
                    current_chain.append(error)
                else:
                    if len(current_chain) >= 3:  # 至少3个错误形成链
                        error_chains.append(current_chain)
                    current_chain = [error]
        
        # 添加最后一个链
        if len(current_chain) >= 3:
            error_chains.append(current_chain)
        
        # 分析错误链
        for chain in error_chains:
            tools_in_chain = [err.action.tool for err in chain]
            error_types_in_chain = [err.error_type.value for err in chain]
            
            insight = LearningInsight(
                insight_type="error_chain",
                description=f"Detected error chain with {len(chain)} consecutive failures",
                confidence=0.7,
                supporting_evidence=[
                    f"Duration: {(chain[-1].timestamp - chain[0].timestamp).total_seconds():.1f} seconds",
                    f"Tools involved: {list(set(tools_in_chain))}",
                    f"Error types: {list(set(error_types_in_chain))}"
                ],
                actionable_advice="Implement early failure detection to prevent error cascades"
            )
            insights.append(insight)
        
        return insights
    
    def generate_behavior_recommendations(self) -> List[str]:
        """基于学习洞察生成行为建议"""
        recommendations = []
        
        # 基于洞察生成建议
        for insight in self.learned_insights:
            if insight.insight_type == "frequent_failure":
                recommendations.append(f"🔧 {insight.actionable_advice}")
            elif insight.insight_type == "temporal_burst":
                recommendations.append(f"⏱️  {insight.actionable_advice}")
            elif insight.insight_type == "problematic_parameter":
                recommendations.append(f"🔍 {insight.actionable_advice}")
            elif insight.insight_type == "ineffective_recovery":
                recommendations.append(f"🔄 {insight.actionable_advice}")
            elif insight.insight_type == "error_chain":
                recommendations.append(f"🚨 {insight.actionable_advice}")
        
        # 添加通用建议
        if not recommendations:
            recommendations.extend([
                "🔧 Implement comprehensive input validation",
                "⏱️  Add timeout handling for all external operations",
                "🔄 Use exponential backoff for retry operations",
                "🚨 Implement health checks for critical dependencies"
            ])
        
        return recommendations
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习总结"""
        insight_types = Counter(insight.insight_type for insight in self.learned_insights)
        
        high_confidence_insights = [
            insight for insight in self.learned_insights 
            if insight.confidence > 0.8
        ]
        
        return {
            "total_insights": len(self.learned_insights),
            "insight_breakdown": dict(insight_types),
            "high_confidence_insights": len(high_confidence_insights),
            "average_confidence": np.mean([i.confidence for i in self.learned_insights]) if self.learned_insights else 0,
            "learning_categories": list(insight_types.keys()),
            "recommendations_count": len(self.generate_behavior_recommendations())
        }
    
    def save_insights(self, filepath: str = "learning_insights.json"):
        """保存学习洞察"""
        data = {
            "insights": [insight.to_dict() for insight in self.learned_insights],
            "summary": self.get_learning_summary(),
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Learning insights saved to {filepath}")
        except Exception as e:
            print(f"❌ Failed to save insights: {e}")


def run_learning_analysis():
    """运行学习分析"""
    print("🧠 Failure Learning Analysis")
    print("=" * 40)
    
    # 加载错误数据
    tracker = ErrorTracker("demo_error_history.json")
    
    if not tracker.error_history:
        print("❌ No error history found. Please run error_tracker.py --create-demo first.")
        return
    
    # 创建学习器
    learner = FailureLearner(tracker)
    
    # 分析失败模式
    insights = learner.analyze_failure_patterns()
    
    print(f"\n📊 Learning Analysis Results:")
    print(f"   Analyzed {len(tracker.error_history)} errors")
    print(f"   Generated {len(insights)} insights")
    
    # 按类型分组显示洞察
    insight_groups = defaultdict(list)
    for insight in insights:
        insight_groups[insight.insight_type].append(insight)
    
    print(f"\n🔍 Discovered Insights:")
    for insight_type, group_insights in insight_groups.items():
        print(f"\n   📋 {insight_type.replace('_', ' ').title()}:")
        for insight in group_insights:
            print(f"      • {insight.description}")
            print(f"        Confidence: {insight.confidence:.1%}")
            print(f"        Advice: {insight.actionable_advice}")
    
    # 生成行为建议
    recommendations = learner.generate_behavior_recommendations()
    print(f"\n💡 Behavior Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # 保存结果
    learner.save_insights()
    
    # 显示学习总结
    summary = learner.get_learning_summary()
    print(f"\n📈 Learning Summary:")
    for key, value in summary.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    return learner


def run_benchmark_test():
    """运行基准测试"""
    print("🏆 Failure Learning Benchmark Test")
    print("=" * 40)
    
    # 创建测试用的错误跟踪器
    tracker = ErrorTracker("benchmark_error_history.json")
    
    # 生成测试数据
    test_scenarios = [
        # 重复的文件错误
        *[{"tool": "file_read", "error_code": "FileNotFoundError", "error_type": ErrorType.ENVIRONMENT} for _ in range(5)],
        # API限速错误
        *[{"tool": "api_call", "error_code": "RateLimitExceeded", "error_type": ErrorType.ENVIRONMENT} for _ in range(4)],
        # 参数错误
        *[{"tool": "calculator", "error_code": "ValueError", "error_type": ErrorType.LOGIC} for _ in range(3)],
        # 超时错误
        *[{"tool": "web_request", "error_code": "TimeoutError", "error_type": ErrorType.TIMEOUT} for _ in range(3)]
    ]
    
    print(f"🔄 Generating {len(test_scenarios)} test errors...")
    
    for i, scenario in enumerate(test_scenarios):
        action = ActionRecord(
            tool=scenario["tool"],
            parameters={"test_param": f"test_value_{i}"}
        )
        
        tracker.track_error(
            error_type=scenario["error_type"],
            error_code=scenario["error_code"],
            message=f"Test error {i+1}",
            action=action,
            context={"test_id": i, "scenario": scenario["tool"]}
        )
    
    # 运行学习分析
    learner = FailureLearner(tracker)
    insights = learner.analyze_failure_patterns()
    
    # 评估结果
    expected_insights = {
        "frequent_failure": 2,  # file_read 和 api_call 应该被识别为频繁失败
        "problematic_parameter": 0,  # 参数都不同，不应该检测到模式
        "temporal_burst": 1   # 可能检测到突发模式
    }
    
    actual_insights = Counter(insight.insight_type for insight in insights)
    
    print(f"\n📊 Benchmark Results:")
    print(f"   Total insights generated: {len(insights)}")
    
    score = 0
    total_tests = len(expected_insights)
    
    for insight_type, expected_count in expected_insights.items():
        actual_count = actual_insights.get(insight_type, 0)
        test_passed = actual_count >= expected_count
        score += 1 if test_passed else 0
        
        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"   {status} {insight_type}: Expected ≥{expected_count}, Got {actual_count}")
    
    final_score = score / total_tests
    print(f"\n🎯 Overall Score: {final_score:.1%} ({score}/{total_tests} tests passed)")
    
    # 清理测试数据
    import os
    try:
        os.remove("benchmark_error_history.json")
        print("🗑️  Benchmark test data cleaned up")
    except:
        pass
    
    return final_score


def main():
    parser = argparse.ArgumentParser(description="Failure Learner Demo")
    parser.add_argument("--analyze", action="store_true", help="Run learning analysis on existing data")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark test")
    parser.add_argument("--full-demo", action="store_true", help="Run full demo with analysis")
    
    args = parser.parse_args()
    
    if args.benchmark:
        score = run_benchmark_test()
        return
    
    if args.analyze:
        learner = run_learning_analysis()
        return
    
    if args.full_demo or not any(vars(args).values()):
        # 默认运行完整演示
        print("🧠 Failure Learning System Demo")
        print("=" * 40)
        print("\n💡 Philosophy: Learn from failures to prevent future mistakes")
        print("   'Failure is the teacher, success is the test'\n")
        
        learner = run_learning_analysis()
        
        if learner:
            print(f"\n📁 Results saved to: learning_insights.json")
            print("\n🚀 Try these commands:")
            print("   python failure_learner.py --analyze")
            print("   python failure_learner.py --benchmark")
        
        return
    
    # 显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
