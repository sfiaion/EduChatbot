from sqlalchemy.orm import Session
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from app.db.neo4j import graph
from ..crud.graph import preload_knowledge_stats
from datetime import datetime

class KnowledgeGraphAnalyzer:
    def __init__(self, db: Session, class_id: int, start_date: datetime, end_date: datetime):
        self.db = db
        self.class_id = class_id
        self.start_date = start_date
        self.end_date = end_date
        self.total_errors, self.daily_errors = preload_knowledge_stats(self.db, self.class_id, self.start_date, self.end_date)

    def analyze_path_dependency(self, center: str):
        # 查所有到 center 的有向依赖路径（深度1~10，防爆炸）
        query = """
            MATCH path = (start:Knowledge)-[:PREREQUISITE*1..10]->(target:Knowledge {name: $center})
            WITH 
                collect({
                    nlist: nodes(path),
                    steps: length(path)
                }) AS all_paths
            WHERE size(all_paths) > 0
    
            WITH 
                all_paths,
                reduce(mx = 0, p IN all_paths | CASE WHEN p.steps > mx THEN p.steps ELSE mx END) AS longest_path,
                reduce(mi = 999999, p IN all_paths | CASE WHEN p.steps < mi THEN p.steps ELSE mi END) AS shortest_path
    
            WITH
                all_paths,
                longest_path,
                shortest_path,
                head([p IN all_paths WHERE p.steps = longest_path]) AS example
    
            UNWIND all_paths AS ap
            WITH 
                ap,
                ap.steps AS steps, 
                ap.nlist AS nodes,
                longest_path,
                shortest_path,
                example
    
            UNWIND range(0, size(nodes)-2) AS idx
            WITH
                nodes[idx] AS node,
                (steps - idx) AS d,
                steps,
                longest_path,
                shortest_path,
                example
            WHERE d >= 1
    
            WITH 
                node.name AS node_name,
                exp( (d - 1) * log(0.7) ) * (1.0 + 0.1 * (toFloat(steps) / toFloat(longest_path))) AS w,
                longest_path,
                shortest_path,
                example
    
            WITH 
                node_name,
                sum(w) AS weight,
                longest_path,
                shortest_path,
                example
    
            ORDER BY weight DESC
    
            WITH 
                collect({node: node_name, weight: weight}) AS weighted_bottlenecks,
                longest_path,
                shortest_path,
                example
    
            RETURN {
                longest_path: longest_path,
                shortest_path: shortest_path,
                weighted_bottlenecks: weighted_bottlenecks[0..5],
                example_path: [n IN example.nlist | n.name]
            } AS result
            """
        result = graph.run(query, center=center).data()
        if not result:
            # 尝试查一下节点是否存在
            check_node = graph.run(
                "MATCH (k:Knowledge {name: $name}) RETURN count(k) AS cnt",
                name=center
            ).data()
            cnt = check_node[0]["cnt"] if check_node else 0
            if cnt == 0:
                return -1, []
            else:
                return 0, []
        data = result[0]["result"]
        longest_path = data["longest_path"]
        bottlenecks = data["weighted_bottlenecks"]

        if longest_path == 1:
            direct = [b["node"] for b in bottlenecks]
            return longest_path, direct
        else:
            top3 = [b["node"] for b in bottlenecks[:3]]
            return longest_path, top3

    def get_all_knowledge_dependencies_by_name(self) -> List[Tuple[str, str]]:
        query = """
        MATCH (p:Knowledge)-[:PREREQUISITE]->(s:Knowledge)
        WHERE p.name IS NOT NULL AND s.name IS NOT NULL
        RETURN p.name AS from_name, s.name AS to_name
        """
        result = graph.run(query).data()
        return [(record["from_name"], record["to_name"]) for record in result]

    def find_top_breakpoints_by_name(self, top_k) -> List[Tuple[str, int]]:
        # 获取所有依赖边
        edges = self.get_all_knowledge_dependencies_by_name()
        # 构建前驱映射
        pred_map: Dict[str, List[str]] = defaultdict(list)
        for from_name, to_name in edges:
            pred_map[to_name].append(from_name)
        # 计算每个节点的“断点差值”
        breakpoints = []
        for name, err in self.total_errors.items():
            preds = pred_map.get(name, [])
            if not preds:
                continue
            max_pred_err = max(self.total_errors.get(p, 0) for p in preds)
            diff = err - max_pred_err
            if diff > 0:
                breakpoints.append((name, diff))
        # 排序取 top-k
        breakpoints.sort(key=lambda x: x[1], reverse=True)
        return breakpoints[:top_k]