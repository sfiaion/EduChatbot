import os
from py2neo import Graph

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")  # ← 不再设默认值！

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is required.")

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))