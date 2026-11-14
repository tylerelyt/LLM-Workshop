"""Read-only, incremental graph retrieval with a verifiable evidence chain."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

Ask = Callable[[str, str], str]
QUESTION = "支付回调进入人工接管后，今天应该通知哪个团队，用哪条值班通道？"
START = "handover"
STEP_LIMIT = 8
SYSTEM = (
    "你在一个只读图谱中调查当前有效的通知路径。"
    "每步只可从本次 JSON 的 available_edges 中选择一个 edge_id。"
    '只返回 JSON 对象，例如 {"edge_id":"E01"}。证据够用或没有可继续调查的线索时，返回 {"stop":true}。'
    "沿有效关系追查归属和当前策略，历史、测试关系仅用于核实。"
)

# The fixture stays inside the retrieval service.
GRAPH = {
    "handover": ("人工接管", "支付回调已进入人工接管，需要核对现行值班路径。", (
        ("现行路由", "route"), ("旧版路由（已退役）", "retired"),
        ("通用操作手册", "manual"), ("演练记录", "drill"),
    )),
    "route": ("支付回调现行路由", "当前路由指向服务别名。归属以别名登记为准。", (
        ("当前服务别名", "alias"), ("架构概览", "diagram"),
    )),
    "alias": ("支付回调服务别名", "迁移后由服务登记中的当前责任团队接管。", (
        ("当前责任团队", "owner"), ("迁移前责任团队（失效）", "old_owner"),
    )),
    "owner": ("支付可靠性组", "服务登记确认支付可靠性组是当前责任团队。", (
        ("现行值班策略", "policy"), ("上季度策略（失效）", "old_policy"),
    )),
    "policy": ("回调人工接管现行策略", "人工接管通过支付可靠性组的支付稳定性值班通道通知。", ()),
    "retired": ("旧版路由", "迁移前通知交易应用组，旧路由已退役。", (
        ("迁移前责任团队（失效）", "old_owner"),
    )),
    "old_owner": ("交易应用组", "该团队在迁移前负责，当前归属已变更。", (
        ("上季度策略（失效）", "old_policy"),
    )),
    "old_policy": ("历史值班策略", "历史记录使用交易应用值班通道。当前已失效。", ()),
    "manual": ("通用操作手册", "人工接管要通知责任方，以当前服务归属和策略为准。", (
        ("回到人工接管条目", "handover"),
    )),
    "drill": ("演练记录", "曾用演练群模拟值班通道。", (("演练配置", "sandbox"),)),
    "sandbox": ("演练配置", "演练群仅用于沙箱，不接收业务通知。", ()),
    "diagram": ("架构概览", "支付回调由路由层分派，示意图不记录责任人。", (
        ("运行历史", "change"), ("容量说明", "capacity"),
    )),
    "change": ("运行历史", "保留了多个版本的迁移记录。", ()),
    "capacity": ("容量说明", "记录吞吐和容量。", ()),
}
# Only a walked, current path qualifies as evidence.
EXPECTED_PATH = (
    ("handover", "现行路由", "route"),
    ("route", "当前服务别名", "alias"),
    ("alias", "当前责任团队", "owner"),
    ("owner", "现行值班策略", "policy"),
)


@dataclass
class Session:
    observations: dict[str, dict] = field(default_factory=dict)
    edges: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    followed: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self._observe(START)

    def _observe(self, node_id: str) -> None:
        if node_id in self.observations:
            return
        title, excerpt, outgoing = GRAPH[node_id]
        hints = []
        for relation, target in outgoing:
            handle = f"E{len(self.edges) + 1:02d}"
            self.edges[handle] = (node_id, relation, target)
            # The target's ID, title, and excerpt stay hidden until this edge is followed.
            hints.append({"edge_id": handle, "relation": relation})
        self.observations[node_id] = {
            "observation_id": node_id, "title": title, "excerpt": excerpt, "outgoing": hints,
        }

    def available(self) -> list[dict]:
        return [
            {"edge_id": handle, "from": source, "relation": relation}
            for handle, (source, relation, target) in self.edges.items()
            if handle not in self.followed and target not in self.observations
        ]

    def follow(self, handle: str) -> dict:
        if handle not in self.edges:
            return {"status": "unknown_edge", "edge_id": handle}
        if handle in self.followed:
            return {"status": "repeated_edge", "edge_id": handle}
        source, relation, target = self.edges[handle]
        if target in self.observations:
            return {"status": "already_observed", "edge_id": handle}
        self.followed.add(handle)
        self._observe(target)
        return {
            "status": "observed", "edge_id": handle, "from": source,
            "relation": relation, "observation_id": target,
        }

    def evidence(self) -> list[dict]:
        followed_edges = {self.edges[handle]: handle for handle in self.followed}
        path = []
        for source, relation, target in EXPECTED_PATH:
            handle = followed_edges.get((source, relation, target))
            if handle is None:
                break
            observed = self.observations[target]
            path.append({
                "edge_id": handle, "from": source, "relation": relation,
                "observation_id": target, "title": observed["title"], "excerpt": observed["excerpt"],
            })
        return path


def one_shot() -> dict:
    """Expand every outgoing edge from the start, without a second round."""
    session = Session()
    initial = session.available()
    for edge in initial:
        session.follow(edge["edge_id"])
    return {
        "expansions": len(initial),
        "observations": list(session.observations.values()),
        "complete": len(session.evidence()) == len(EXPECTED_PATH),
        "why": "起点的现行路由只指向服务别名。该轮未取得当前责任团队及现行值班策略。",
    }


def _offline_edge(available: list[dict]) -> str:
    """Select by observed relation text, without accessing the graph or checker."""
    preferred = {"现行路由", "当前服务别名", "当前责任团队", "现行值班策略"}
    return next(
        (edge["edge_id"] for edge in available if edge["relation"] in preferred),
        available[0]["edge_id"],
    )


def run(ask: Ask | None = None) -> dict:
    session = Session()
    trace: list[dict] = []
    for _ in range(STEP_LIMIT):
        available = session.available()
        if not available or len(session.evidence()) == len(EXPECTED_PATH):
            break
        if ask is None:
            handle = _offline_edge(available)
        else:
            context = json.dumps({
                "question": QUESTION,
                "steps_remaining": STEP_LIMIT - len(trace),
                "observations": list(session.observations.values()),
                "available_edges": available,
                "last_step": trace[-1] if trace else None,
            }, ensure_ascii=False)
            reply = ask(SYSTEM, context)
            try:
                action = json.loads(reply)
                if isinstance(action, dict) and action.get("stop") is True:
                    trace.append({"status": "stopped"})
                    break
                handle = action["edge_id"]
                if not isinstance(handle, str) or len(handle) > 16:
                    raise ValueError("invalid edge handle")
            except (TypeError, KeyError, ValueError):
                trace.append({"status": "invalid_action"})
                continue
        trace.append(session.follow(handle))

    evidence = session.evidence()
    complete = len(evidence) == len(EXPECTED_PATH)
    return {
        "question": QUESTION,
        "mode": "offline" if ask is None else "model",
        "step_limit": STEP_LIMIT,
        "one_shot": one_shot(),
        "trace": trace,
        "observations": list(session.observations.values()),
        "evidence": evidence,
        "complete": complete,
        "answer": (
            {"team": evidence[-2]["title"], "policy": evidence[-1]["excerpt"]}
            if complete else None
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
