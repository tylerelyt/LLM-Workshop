#!/usr/bin/env python3
"""
Enterprise NL2SQL Demo in a Single File
========================================

A refactored, comprehensive demonstration of a Text-to-SQL pipeline 
showcasing modular design within a single script. It handles a complex, 
multi-table join BI scenario.

Architecture Highlights:
1.  **Config-Driven**: A central `CONFIG` dictionary manages all settings.
2.  **Modular Classes**: Internal classes (`DBManager`, `VectorStore`, `LLMProvider`) 
    encapsulate specific responsibilities.
3.  **Orchestrator Pattern**: The main `NL2SQLPipeline` class coordinates the workflow.
4.  **Complex BI Scenario**: Uses a 5-table schema for realistic sales analysis.

Author: Tyler (Refactored by Gemini)
License: MIT
"""

import os
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Conditional imports for LLM providers
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# --- Configuration Block ----------------------------------------------------
# All settings are managed here, replacing an external config file for simplicity.
CONFIG = {
    "database": {
        "path": "enterprise_bi.db",
    },
    "embedding_model": "text-embedding-v4",
    "llm": {
        "provider": "dashscope",  # or "openai"
        "api_key_env": "DASHSCOPE_API_KEY", # or "OPENAI_API_KEY"
        "models": {
            "sql_generation": "qwen-plus",
            "answer_generation": "qwen-plus",
        }
    },
    "prompts": {
        "sql_generation": """
你是一位SQLite数据库专家。根据给定的数据库模式和自然语言问题，生成准确且可执行的SQL查询。

**重要约束**：
1. 只能使用提供的数据库模式中明确存在的表和字段
2. 如果问题要求的数据在给定的DDL中不存在，必须拒绝生成SQL
3. 拒绝时返回：SCHEMA_INSUFFICIENT: [具体说明缺少什么数据]

### 数据库模式:
{schema_context}

### 问题:
{question}

### 要求:
- 如果所需字段都存在：返回纯SQL语句，不要有任何解释或markdown格式
- 如果缺少必要字段：返回 SCHEMA_INSUFFICIENT: [说明原因]

SQL:
""",
        "answer_generation": """
你是一位专业的商业智能助手。基于用户的问题、SQL查询和数据结构摘要，提供有价值的分析回答。

注意：出于数据安全考虑，你收到的是数据结构摘要而非实际数据值。请基于查询逻辑和数据结构提供专业分析。

### 用户问题:
{question}

### 执行的SQL查询:
{sql_query}

### 数据结构摘要:
{data_summary}

### 分析要求:
1. 基于SQL查询逻辑分析业务问题
2. 解释查询涉及的业务指标和关系
3. 根据数据结构提供合理的业务洞察
4. 提供数据驱动的建议（如适用）

### 专业分析:
"""
    }
}

# --- Logging Setup ----------------------------------------------------------
# 配置日志同时输出到控制台和文件
log_format = '%(asctime)s - %(levelname)s - [%(name)s] %(message)s'

# 创建logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 清除已有的handlers（避免重复）
if logger.handlers:
    logger.handlers.clear()

# 创建控制台handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(log_format)
console_handler.setFormatter(console_formatter)

# 创建文件handler
file_handler = logging.FileHandler('nl2sql_demo_info.log', mode='w', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(log_format)
file_handler.setFormatter(file_formatter)

# 添加handlers到logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# --- Data Classes -----------------------------------------------------------
@dataclass
class TableSchema:
    """Represents a database table schema with metadata."""
    name: str
    ddl: str
    description: str
    
@dataclass
class QueryResult:
    """Represents the result of a SQL query execution."""
    success: bool
    data: List[Dict[str, Any]]
    sql: str
    error: Optional[str] = None

# --- Modular Components -----------------------------------------------------

class DBManager:
    """
    Manages all database interactions, including schema creation and querying.
    In a real app, this would handle connection pooling (e.g., with SQLAlchemy).
    """
    def __init__(self, db_config: Dict[str, Any]):
        self.db_path = db_config['path']
        logger.info(f"DBManager initialized for database: {self.db_path}")
        self._init_database()
    
    def _init_database(self):
        """Initializes the database and creates the 5-table enterprise schema if not present."""
        logger.info("Initializing database schema...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'")
        if cursor.fetchone():
            logger.info("Database schema already exists. Skipping creation.")
            conn.close()
            return

        logger.info("Creating enterprise BI schema (5 tables)...")
        self._create_enterprise_schema(cursor)
        self._insert_sample_data(cursor)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")

    def _create_enterprise_schema(self, cursor: sqlite3.Cursor):
        """Defines and creates the 10-table schema with rich metadata for complex enterprise analysis."""
        # Drop existing tables
        tables_to_drop = ['sales', 'employees', 'departments', 'products', 'regions', 
                         'customers', 'orders', 'suppliers', 'inventory', 'promotions']
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")

        # 1. 部门表 - 组织架构信息
        cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY, 
            name TEXT NOT NULL UNIQUE, -- 部门名称，如：销售部、技术部、财务部
            description TEXT, -- 部门职能描述
            manager_id INTEGER, -- 部门经理的员工ID，用于部门负责人分析
            budget REAL NOT NULL, -- 部门年度预算金额
            location TEXT -- 部门办公地点
        );""")
        
        # 2. 地区表 - 销售区域和税务信息
        cursor.execute("""
        CREATE TABLE regions (
            id INTEGER PRIMARY KEY, 
            name TEXT NOT NULL UNIQUE, -- 地区名称，如：华北、华东、华南、欧洲等
            country TEXT NOT NULL, -- 所属国家
            timezone TEXT, -- 时区信息
            tax_rate REAL -- 该地区的税率，用于税务分析和价格敏感性分析
        );""")
        
        # 3. 产品表 - 商品信息和成本数据
        cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY, 
            name TEXT NOT NULL, -- 产品名称，如：笔记本电脑、智能手机等
            category TEXT NOT NULL, -- 产品类别，如：电脑、手机、家电、服装
            price REAL NOT NULL, -- 销售价格
            cost REAL NOT NULL, -- 产品成本，用于利润分析
            supplier_id INTEGER, -- 供应商ID，关联供应商表
            launch_date TEXT, -- 产品上市日期
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        );""")
        
        # 4. 员工表 - 人力资源和组织层级
        cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL, -- 员工姓名
            department_id INTEGER NOT NULL, -- 所属部门ID
            position TEXT, -- 职位名称，如：销售经理、开发工程师
            salary REAL, -- 员工薪资，用于成本和绩效分析
            hire_date TEXT, -- 入职日期
            manager_id INTEGER, -- 直属上级经理ID，用于员工层级关系和管理效能分析，也可称为reports_to或supervisor_id
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (manager_id) REFERENCES employees (id)
        );""")
        
        # 5. 客户表 - 客户信息和分类
        cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL, -- 客户名称或公司名
            email TEXT, -- 联系邮箱
            region_id INTEGER NOT NULL, -- 所属销售区域
            customer_type TEXT, -- 客户类型：个人客户、企业客户、代理商、分销商、零售商等，用于客户行为分析
            registration_date TEXT, -- 注册日期
            credit_limit REAL, -- 信用额度
            FOREIGN KEY (region_id) REFERENCES regions (id)
        );""")
        
        # 6. 供应商表 - 供应链管理
        cursor.execute("""
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL, -- 供应商名称
            region_id INTEGER NOT NULL, -- 供应商所在地区
            contact_email TEXT, -- 联系邮箱
            phone TEXT, -- 联系电话
            quality_rating REAL, -- 供应商质量评级（1-5分），用于供应商绩效分析
            FOREIGN KEY (region_id) REFERENCES regions (id)
        );""")
        
        # 7. 订单表 - 销售订单主表
        cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL, -- 下单客户ID
            employee_id INTEGER NOT NULL, -- 负责销售员工ID，用于销售绩效分析
            order_date TEXT NOT NULL, -- 订单日期，用于时间分析和季节性分析
            total_amount REAL, -- 订单总金额
            status TEXT, -- 订单状态：已完成、处理中、已取消、Promotion（促销期间）等
            shipping_region_id INTEGER, -- 发货地区ID
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (shipping_region_id) REFERENCES regions (id)
        );""")
        
        # 8. 销售明细表 - 订单商品明细，相当于订单明细表(order_items/order_details)
        cursor.execute("""
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY, 
            order_id INTEGER NOT NULL, -- 关联订单ID
            product_id INTEGER NOT NULL, -- 销售产品ID
            quantity INTEGER NOT NULL, -- 销售数量
            unit_price REAL NOT NULL, -- 商品单价
            discount REAL DEFAULT 0, -- 折扣率（0-1之间），用于促销效果分析
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );""")
        
        # 9. 库存表 - 库存管理和风险分析
        cursor.execute("""
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL, -- 产品ID
            region_id INTEGER NOT NULL, -- 库存所在地区
            quantity_in_stock INTEGER, -- 当前库存数量
            reorder_level INTEGER, -- 再订购水平，用于库存积压风险分析和补货预警
            last_updated TEXT, -- 最后更新时间
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (region_id) REFERENCES regions (id)
        );""")
        
        # 10. 促销活动表 - 营销活动管理
        cursor.execute("""
        CREATE TABLE promotions (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL, -- 促销活动名称
            product_id INTEGER, -- 促销产品ID，NULL表示全品类促销
            region_id INTEGER, -- 促销地区ID，NULL表示全地区
            discount_rate REAL, -- 促销折扣率，用于促销效果分析和紧急补货预警
            start_date TEXT, -- 促销开始日期
            end_date TEXT, -- 促销结束日期，用于识别即将过期的促销活动
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (region_id) REFERENCES regions (id)
        );""")
        
        logger.info("10 tables created for complex enterprise scenario.")
    
    def _insert_sample_data(self, cursor: sqlite3.Cursor):
        """Inserts comprehensive sample data for complex multi-table queries."""
        # 1. 部门数据
        cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, ?, ?)", [
            (1, '电子产品', '消费电子产品销售部门', 1, 2000000, '北京'),
            (2, '家居用品', '家居生活用品部门', 3, 800000, '上海'),
            (3, '服装', '时尚服装部门', 4, 1200000, '广州'),
            (4, '市场营销', '品牌推广和市场分析', 5, 600000, '深圳'),
            (5, '人力资源', '员工管理和招聘', 6, 400000, '杭州')
        ])
        
        # 2. 地区数据
        cursor.executemany("INSERT INTO regions VALUES (?, ?, ?, ?, ?)", [
            (1, '华北', '中国', 'GMT+8', 0.13),
            (2, '华东', '中国', 'GMT+8', 0.13),
            (3, '华南', '中国', 'GMT+8', 0.13),
            (4, '北美', '美国', 'GMT-5', 0.08),
            (5, '欧洲', '德国', 'GMT+1', 0.19),
            (6, '东南亚', '新加坡', 'GMT+8', 0.07)
        ])
        
        # 3. 供应商数据
        cursor.executemany("INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?)", [
            (1, '深圳科技有限公司', 3, 'tech@shenzhen.com', '0755-1234567', 4.5),
            (2, '江苏制造集团', 2, 'sales@jiangsu.com', '025-7654321', 4.2),
            (3, '广东纺织公司', 3, 'textile@guangdong.com', '020-9876543', 4.0),
            (4, '北京创新科技', 1, 'innovation@beijing.com', '010-5555555', 4.8)
        ])
        
        # 4. 产品数据
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (1, '笔记本电脑', '电脑', 1200, 800, 1, '2023-01-15'),
            (2, '智能手机', '手机', 800, 500, 1, '2023-03-20'),
            (3, '平板电脑', '电脑', 600, 400, 1, '2023-05-10'),
            (4, '咖啡机', '家电', 150, 100, 2, '2023-02-01'),
            (5, '空气净化器', '家电', 300, 200, 2, '2023-04-15'),
            (6, 'T恤', '上衣', 25, 15, 3, '2023-03-01'),
            (7, '牛仔裤', '裤子', 80, 50, 3, '2023-06-01'),
            (8, '无线耳机', '数码', 200, 120, 4, '2023-07-01')
        ])
        
        # 5. 员工数据
        cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (1, '张三', 1, '销售经理', 120000, '2020-01-15', None),
            (2, '李四', 1, '销售代表', 80000, '2021-03-22', 1),
            (3, '王五', 2, '产品经理', 95000, '2019-07-30', None),
            (4, '赵六', 3, '设计师', 75000, '2022-02-14', None),
            (5, '钱七', 4, '市场专员', 65000, '2021-11-08', None),
            (6, '孙八', 5, 'HR专员', 55000, '2023-01-10', None),
            (7, '周九', 1, '销售代表', 85000, '2022-09-05', 1),
            (8, '吴十', 2, '采购员', 70000, '2020-12-01', 3)
        ])
        
        # 6. 客户数据
        cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (1, '北京科技公司', 'beijing@tech.com', 1, '企业客户', '2022-01-01', 500000),
            (2, '上海贸易公司', 'shanghai@trade.com', 2, '企业客户', '2022-03-15', 300000),
            (3, '广州零售商', 'guangzhou@retail.com', 3, '零售商', '2022-05-20', 200000),
            (4, '个人客户张先生', 'zhang@personal.com', 1, '个人客户', '2023-01-10', 50000),
            (5, '个人客户李女士', 'li@personal.com', 2, '个人客户', '2023-02-15', 30000),
            (6, '海外代理商A', 'agent@overseas.com', 4, '代理商', '2022-08-01', 1000000),
            (7, '欧洲分销商', 'eu@distributor.com', 5, '分销商', '2022-10-01', 800000)
        ])
        
        # 7. 订单数据
        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (1, 1, 1, '2024-01-15', 15000, '已完成', 1),
            (2, 2, 2, '2024-02-20', 8000, '已完成', 2),
            (3, 3, 1, '2024-03-10', 2500, '已完成', 3),
            (4, 4, 7, '2024-04-05', 1200, '已完成', 1),
            (5, 5, 2, '2024-05-18', 300, '已完成', 2),
            (6, 6, 1, '2024-06-22', 50000, '处理中', 4),
            (7, 7, 7, '2024-07-01', 25000, '已发货', 5),
            (8, 1, 1, '2024-07-15', 18000, '已完成', 1),
            (9, 3, 2, '2024-08-01', 4000, '处理中', 3)
        ])
        
        # 8. 销售明细数据
        cursor.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)", [
            (1, 1, 1, 10, 1200, 0.1),    # 北京科技公司买笔记本
            (2, 1, 2, 5, 800, 0.05),     # 北京科技公司买手机
            (3, 2, 2, 10, 800, 0.0),     # 上海贸易公司买手机
            (4, 3, 4, 10, 150, 0.0),     # 广州零售商买咖啡机
            (5, 3, 6, 50, 25, 0.0),      # 广州零售商买T恤
            (6, 4, 1, 1, 1200, 0.0),     # 张先生买笔记本
            (7, 5, 5, 1, 300, 0.0),      # 李女士买空气净化器
            (8, 6, 1, 30, 1200, 0.15),   # 海外代理商买笔记本
            (9, 6, 3, 20, 600, 0.1),     # 海外代理商买平板
            (10, 7, 2, 25, 800, 0.12),   # 欧洲分销商买手机
            (11, 7, 8, 10, 200, 0.08),   # 欧洲分销商买耳机
            (12, 8, 1, 15, 1200, 0.08),  # 北京科技公司再次购买
            (13, 9, 7, 40, 80, 0.0)      # 广州零售商买牛仔裤
        ])
        
        # 9. 库存数据
        cursor.executemany("INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?)", [
            (1, 1, 1, 100, 20, '2024-08-01'),  # 华北笔记本库存
            (2, 1, 2, 80, 15, '2024-08-01'),   # 华东笔记本库存
            (3, 2, 1, 200, 50, '2024-08-01'),  # 华北手机库存
            (4, 2, 3, 150, 30, '2024-08-01'),  # 华南手机库存
            (5, 4, 2, 50, 10, '2024-08-01'),   # 华东咖啡机库存
            (6, 6, 3, 500, 100, '2024-08-01'), # 华南T恤库存
            (7, 8, 5, 80, 20, '2024-08-01')    # 欧洲耳机库存
        ])
        
        # 10. 促销活动数据
        cursor.executemany("INSERT INTO promotions VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (1, '春季电脑促销', 1, 1, 0.15, '2024-03-01', '2024-03-31'),
            (2, '夏季手机优惠', 2, 2, 0.1, '2024-06-01', '2024-06-30'),
            (3, '全球T恤节', 6, None, 0.2, '2024-07-01', '2024-07-15'),
            (4, '家电清仓', None, 2, 0.25, '2024-08-01', '2024-08-31')
        ])
        
        logger.info("Complex sample data inserted for 10-table scenario.")
    
    def get_all_schemas(self) -> List[TableSchema]:
        """Retrieves DDL and descriptions for all tables in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        conn.close()
        
        # Enhanced descriptions for complex scenario
        descriptions = {
            'departments': '部门信息表，包含部门预算、位置、经理等详细信息。',
            'regions': '地区表，存储全球各地区的时区、税率等信息。',
            'products': '产品目录表，包含价格、成本、供应商、上市时间等完整产品信息。',
            'employees': '员工档案表，记录职位、薪资、入职时间、上级关系等。',
            'customers': '客户信息表，包含客户类型、信用额度、注册时间等。',
            'suppliers': '供应商管理表，记录联系方式、质量评级等供应商信息。',
            'orders': '订单主表，记录客户订单的基本信息和状态。',
            'sales': '销售明细表，记录每个订单中具体产品的销售情况。',
            'inventory': '库存管理表，跟踪各地区产品库存量和补货提醒。',
            'promotions': '促销活动表，管理产品和地区的优惠活动信息。'
        }

        return [TableSchema(name=t[0], ddl=t[1], description=descriptions.get(t[0], '')) for t in tables]

    def execute_sql(self, sql: str) -> QueryResult:
        """Executes a given SQL query and returns the result."""
        logger.info(f"Executing SQL: {sql.strip()}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                data = [dict(row) for row in rows]
                logger.info(f"SQL executed successfully, returned {len(data)} rows.")
                return QueryResult(success=True, data=data, sql=sql)
        except Exception as e:
            logger.error(f"SQL execution failed: {e}", exc_info=True)
            return QueryResult(success=False, data=[], error=str(e), sql=sql)

class VectorStore:
    """Handles embedding creation and retrieval of relevant schemas using DashScope."""
    def __init__(self, model_name: str = "text-embedding-v4"):
        try:
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Please run 'pip install openai'.")
            self.model_name = model_name
            self.client = OpenAI(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            logger.info(f"VectorStore initialized with DashScope model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DashScope embedding client: {e}", exc_info=True)
            raise
        self.schemas: List[TableSchema] = []
        self.schema_embeddings: Optional[np.ndarray] = None

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings using DashScope API"""
        try:
            # 批量处理文本
            all_embeddings = []
            for text in texts:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=text,
                    dimensions=1024,
                    encoding_format="float"
                )
                all_embeddings.append(response.data[0].embedding)
            return np.array(all_embeddings)
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            raise

    def build_embeddings(self, schemas: List[TableSchema]):
        """Creates and stores vector embeddings for the given schemas."""
        self.schemas = schemas
        if not self.schemas:
            logger.warning("No schemas provided to build embeddings.")
            return
            
        # Create text descriptions for embedding
        descriptions = []
        for schema in self.schemas:
            # 使用表名+描述+DDL的组合作为embedding输入
            text = f"Table: {schema.name}\nDescription: {schema.description}\nDDL: {schema.ddl}"
            descriptions.append(text)
        
        logger.info(f"Creating embeddings for {len(descriptions)} schemas...")
        self.schema_embeddings = self.get_embeddings(descriptions)
        logger.info(f"Built embeddings for {len(self.schemas)} schemas.")

    def _extract_columns_from_ddl(self, ddl: str) -> str:
        """Extract column names from DDL for better context."""
        try:
            lines = ddl.strip().split('\n')
            column_lines = lines[1:-1] # Exclude CREATE TABLE and closing parenthesis
            return ", ".join([line.strip().split()[0] for line in column_lines])
        except Exception:
            return ""
    
    def retrieve_relevant_schemas(self, question: str, top_k: int = 5) -> List[TableSchema]:
        """Finds the most relevant schemas for a question using cosine similarity."""
        if self.schema_embeddings is None or not self.schemas:
            logger.warning("Embeddings not built. Cannot retrieve schemas.")
            return []
        
        question_embedding = self.get_embeddings([question])
        similarities = cosine_similarity(question_embedding, self.schema_embeddings)[0]
        
        # Get top-k indices, ensuring we don't exceed the number of available schemas
        k = min(top_k, len(self.schemas))
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        relevant_schemas = [self.schemas[i] for i in top_indices]
        logger.info(f"Retrieved {len(relevant_schemas)} relevant schemas for the question.")
        for i in top_indices:
            logger.info(f"  - {self.schemas[i].name} (Similarity: {similarities[i]:.4f})")
            
        return relevant_schemas
    
    def multi_path_retrieve_schemas(self, question: str, llm_provider, top_k_per_path: int = 3) -> List[TableSchema]:
        """使用LLM分析查询维度，然后多路召回DDL表结构"""
        
        # 第一步：让LLM分析需要哪些数据维度
        analysis_prompt = f"""
分析这个业务查询需要哪些数据维度，输出3-5个具体的查询方向。
每个方向要使用最直接、简洁的关键词，便于匹配数据表名称。

查询: {question}

输出格式，每行一个维度：
employees
sales
products
customers
orders
"""
        
        logger.info("LLM analyzing query dimensions...")
        dimensions_text = llm_provider._call_llm(analysis_prompt, "qwen-plus")
        
        # 解析分析结果
        dimensions = [dim.strip() for dim in dimensions_text.split('\n') if dim.strip()]
        logger.info(f"Identified {len(dimensions)} query dimensions: {dimensions}")
        
        # 第二步：为每个维度进行向量检索
        all_retrieved_schemas = []
        seen_table_names = set()
        
        for dimension in dimensions:
            logger.info(f"Retrieving dimension: {dimension}")
            
            dimension_embedding = self.get_embeddings([dimension])
            similarities = cosine_similarity(dimension_embedding, self.schema_embeddings)[0]
            
            # 为每个维度检索top_k_per_path个表
            k = min(top_k_per_path, len(self.schemas))
            top_indices = np.argsort(similarities)[-k:][::-1]
            
            for i in top_indices:
                schema = self.schemas[i]
                if schema.name not in seen_table_names:
                    all_retrieved_schemas.append(schema)
                    seen_table_names.add(schema.name)
                    logger.info(f"  Retrieved {schema.name} (Similarity: {similarities[i]:.4f})")
        
        logger.info(f"Multi-path retrieval completed, retrieved {len(all_retrieved_schemas)} relevant tables")
        return all_retrieved_schemas
    
class LLMProvider:
    """A wrapper for LLM API calls using OpenAI-compatible interface."""
    def __init__(self, llm_config: Dict[str, Any]):
        self.provider = llm_config.get("provider")
        self.models = llm_config.get("models", {})
        api_key = os.environ.get(llm_config.get("api_key_env", ""))
        
        if not api_key:
            raise ValueError(f"API key not found. Please set the {llm_config.get('api_key_env')} environment variable.")

        if OpenAI is None:
            raise ImportError("OpenAI SDK not installed. Please run 'pip install openai'.")
        
        # 使用OpenAI兼容接口调用DashScope
        if self.provider == "dashscope":
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        elif self.provider == "openai":
            self.client = OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        logger.info(f"LLMProvider initialized for '{self.provider}'.")

    def _call_llm(self, prompt: str, model: str) -> str:
        """Internal method to make the actual API call."""
        logger.info(f"Calling LLM ({self.provider}, model: {model})...")
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM API call failed: {e}", exc_info=True)
            return f"Error: LLM call failed. {e}"

    def generate_sql(self, prompt: str) -> str:
        """Generates SQL from a prompt."""
        model = self.models.get("sql_generation", "qwen-plus")
        sql = self._call_llm(prompt, model)
        # Clean up potential markdown formatting
        return sql.replace("```sql", "").replace("```", "").strip()
    
    def generate_answer(self, prompt: str) -> str:
        """Generates a natural language answer from a prompt."""
        model = self.models.get("answer_generation", "qwen-plus")
        return self._call_llm(prompt, model).strip()

# --- Main Pipeline Orchestrator ----------------------------------------------

class NL2SQLPipeline:
    """Orchestrates the Text-to-SQL process using modular components."""
    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing NL2SQL Pipeline...")
        self.db_manager = DBManager(config['database'])
        
        # Initialize vector store
        self.vector_store = VectorStore(config['embedding_model'])
        logger.info(f"VectorStore initialized with embedding model: {config['embedding_model']}")
        
        # Initialize LLM provider  
        self.llm_provider = LLMProvider(llm_config=config['llm'])
        logger.info(f"LLMProvider initialized for '{config['llm']['provider']}'.")
        
        # Create embeddings for all schemas
        all_schemas = self.db_manager.get_all_schemas()
        logger.info(f"Creating embeddings for {len(all_schemas)} schemas...")
        self.vector_store.build_embeddings(all_schemas)
        logger.info(f"Built embeddings for {len(all_schemas)} schemas.")
        
        # Load prompt templates
        self.sql_prompt_template = config['prompts']['sql_generation']
        self.answer_prompt_template = config['prompts']['answer_generation']
        logger.info("NL2SQL Pipeline initialized successfully.")

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Executes the full Text-to-SQL pipeline for a given question.
        """
        import time
        start_time = time.time()
        
        logger.info("=" * 80)
        logger.info(f"Processing question: {question}")
        logger.info("=" * 80)

        # 1. Retrieve relevant schemas using multi-path approach
        logger.info("Step 1: Starting multi-path vector retrieval...")
        retrieval_start = time.time()
        relevant_schemas = self.vector_store.multi_path_retrieve_schemas(question, self.llm_provider, top_k_per_path=4)
        retrieval_time = time.time() - retrieval_start
        
        logger.info(f"Vector retrieval completed in {retrieval_time:.2f}s")
        logger.info(f"Retrieved {len(relevant_schemas)} relevant tables: {[s.name for s in relevant_schemas]}")
        
        schema_context = "\n\n".join([f"--- Table: {s.name} ---\n{s.ddl}" for s in relevant_schemas])
        logger.info(f"Schema context built, length: {len(schema_context)} characters")

        # 2. Generate SQL
        logger.info("Step 2: Starting SQL generation...")
        sql_start = time.time()
        sql_prompt = self.sql_prompt_template.format(schema_context=schema_context, question=question)
        logger.info(f"SQL prompt length: {len(sql_prompt)} characters")
        
        sql_query = self.llm_provider.generate_sql(sql_prompt)
        sql_time = time.time() - sql_start
        
        logger.info(f"SQL generation completed in {sql_time:.2f}s")
        
        # Check if LLM rejected the query due to insufficient schema
        if sql_query.strip().startswith("SCHEMA_INSUFFICIENT:"):
            logger.warning("LLM rejected SQL generation due to insufficient DDL")
            logger.warning(f"Rejection reason: {sql_query.strip()}")
            
            total_time = time.time() - start_time
            return {
                'question': question,
                'relevant_schemas': [s.name for s in relevant_schemas],
                'sql_query': None,
                'data': [],
                'answer': f"Current database structure cannot satisfy the query requirements. {sql_query.replace('SCHEMA_INSUFFICIENT:', '').strip()}",
                'query_success': False,
                'schema_insufficient': True,
                'performance': {
                    'retrieval_time': retrieval_time,
                    'sql_generation_time': sql_time,
                    'execution_time': 0,
                    'answer_generation_time': 0,
                    'total_time': total_time
                }
            }
        
        logger.info(f"Generated SQL: {sql_query}")

        # 3. Execute SQL
        logger.info("Step 3: Starting database query execution...")
        exec_start = time.time()
        query_result = self.db_manager.execute_sql(sql_query)
        exec_time = time.time() - exec_start
        
        if query_result.success:
            logger.info(f"Query executed successfully in {exec_time:.2f}s")
            logger.info(f"Returned {len(query_result.data)} records")
            if query_result.data:
                logger.info(f"Sample data available: {len(query_result.data)} records")
        else:
            logger.error(f"Query execution failed in {exec_time:.2f}s")
            logger.error(f"Error: {query_result.error}")

        # 4. Generate Answer (if SQL was successful)
        logger.info("Step 4: Starting natural language answer generation...")
        answer_start = time.time()
        answer = ""
        
        if query_result.success:
            if not query_result.data:
                answer = "I found relevant information, but no data matched your specific conditions."
                logger.info("Query successful but no data, returning standard prompt")
            else:
                # 生成数据摘要而不是完整数据，避免数据泄露
                data_summary = self._create_data_summary(query_result.data)
                logger.info(f"Preparing answer generation, data summary length: {len(data_summary)} characters")
                
                answer_prompt = self.answer_prompt_template.format(
                    question=question,
                    sql_query=sql_query,
                    data_summary=data_summary
                )
                logger.info(f"Answer generation prompt length: {len(answer_prompt)} characters")
                
                answer = self.llm_provider.generate_answer(answer_prompt)
                logger.info(f"Answer length: {len(answer)} characters")
        else:
            answer = f"Sorry, an error occurred while answering your question. Database reported: {query_result.error}"
            logger.info("Due to query failure, returning error message")
        
        answer_time = time.time() - answer_start
        total_time = time.time() - start_time
        
        logger.info(f"Answer generation completed in {answer_time:.2f}s")
        logger.info("Performance statistics:")
        logger.info(f"   Retrieval: {retrieval_time:.2f}s")
        logger.info(f"   SQL Generation: {sql_time:.2f}s") 
        logger.info(f"   Query Execution: {exec_time:.2f}s")
        logger.info(f"   Answer Generation: {answer_time:.2f}s")
        logger.info(f"   Total time: {total_time:.2f}s")
        logger.info("=" * 80)
        logger.info(f"Question processing completed: {question[:50]}...")
        logger.info("=" * 80)
        
        return {
            "question": question,
            "relevant_schemas": [s.name for s in relevant_schemas],
            "sql_query": query_result.sql,
            "query_success": query_result.success,
            "query_error": query_result.error,
            "data": query_result.data,
            "answer": answer,
            "performance": {
                "retrieval_time": retrieval_time,
                "sql_generation_time": sql_time,
                "execution_time": exec_time,
                "answer_generation_time": answer_time,
                "total_time": total_time
            }
        }

    def _create_data_summary(self, data: List[Dict[str, Any]]) -> str:
        """创建数据摘要，避免泄露敏感信息，只提供结构化统计信息"""
        if not data:
            return "No data available."

        # 提取所有列名和数据类型信息
        all_columns = set()
        column_types = {}
        
        for record in data:
            all_columns.update(record.keys())
            for key, value in record.items():
                if key not in column_types:
                    column_types[key] = type(value).__name__

        # 生成安全的数据摘要（不包含实际数据值）
        summary_data = {
            "total_records": len(data),
            "columns_info": {
                col: column_types.get(col, "unknown") 
                for col in sorted(list(all_columns))
            },
            "data_structure": "Multi-table query results with business metrics",
            "privacy_note": "Actual data values omitted for security"
        }
        
        return json.dumps(summary_data, indent=2, ensure_ascii=False)

# --- Demo Execution ---------------------------------------------------------
def run_demo():
    """Sets up the pipeline and runs a demo with complex BI questions."""
    print("=" * 60)
    print("🤖 企业级中文NL2SQL自动演示")
    print("=" * 60)

    try:
        # Check for API key before initializing
        api_key_env = CONFIG['llm']['api_key_env']
        if not os.environ.get(api_key_env):
            print(f"\n❌ 错误：环境变量 '{api_key_env}' 未设置。")
            print("请设置您的API密钥以继续。")
            return
    
        pipeline = NL2SQLPipeline(CONFIG)
        
        # 复杂的多表联查问题集合
        demo_questions = [
            {
                "question": "分析不同地区税率对订单金额和客户购买决策的影响，找出最具价格敏感性的客户群体。",
                "description": "🌍 税率影响分析 - 多表联查 + 价格敏感性分析"
            },
            {
                "question": "分析各地区的销售业绩和产品表现：统计每个地区的总销售额、畅销产品类别、客户类型分布，以及平均折扣水平，识别出销售潜力最大的地区和产品组合。",
                "description": "📈 地区销售潜力分析 - 8表联查 + 产品表现 + 客户细分"
            }
        ]
        
        print(f"\nEnterprise complex scenario demo started - showcasing the most challenging multi-table query analysis")
        print("Database scale: 10 core business tables with complex relationships and business logic")
        print("Challenge difficulty: Tax impact analysis - requires intelligent identification of 8+ related tables for price sensitivity analysis")
        print("=" * 90)
        
        # 统计信息
        import time
        total_start_time = time.time()
        demo_stats = {
            "total_questions": len(demo_questions),
            "successful_queries": 0,
            "failed_queries": 0,
            "total_tables_used": set(),
            "total_execution_time": 0,
            "performance_breakdown": [],
            "schema_insufficient_queries": 0
        }
        
        logger.info("Starting enterprise NL2SQL demo")
        logger.info(f"Demo configuration: {len(demo_questions)} complex questions, 10 tables")
        logger.info("=" * 80)
        
        for i, demo in enumerate(demo_questions, 1):
            question = demo["question"]
            description = demo["description"]
            
            print(f"\n[Challenge {i}/{len(demo_questions)}] {description}")
            print(f"Question: {question}")
            print("Processing...")
            
            logger.info("=" * 30)
            logger.info(f"Demo {i}/{len(demo_questions)} starting")
            logger.info(f"Type: {description}")
            logger.info(f"Question: {question}")
            logger.info("=" * 30)
            
            demo_start_time = time.time()
            result = pipeline.ask(question)
            demo_time = time.time() - demo_start_time
            
            # 统计信息更新
            demo_stats["total_execution_time"] += demo_time
            demo_stats["total_tables_used"].update(result['relevant_schemas'])
            
            if result['query_success']:
                demo_stats["successful_queries"] += 1
                logger.info(f"Demo {i} completed successfully")
            elif result.get('schema_insufficient', False):
                demo_stats["failed_queries"] += 1
                demo_stats.setdefault("schema_insufficient_queries", 0)
                demo_stats["schema_insufficient_queries"] += 1
                logger.warning(f"Demo {i} rejected due to insufficient DDL")
            else:
                demo_stats["failed_queries"] += 1
                logger.error(f"Demo {i} execution failed")
            
            # 记录演示统计
            demo_stat = {
                "demo_number": i,
                "description": description,
                "success": result['query_success'],
                "schema_insufficient": result.get('schema_insufficient', False),
                "tables_used": len(result['relevant_schemas']),
                "table_names": result['relevant_schemas'],
                "data_records": len(result['data']) if result['query_success'] else 0,
                "execution_time": demo_time,
                "performance": result.get('performance', {})
            }
            demo_stats["performance_breakdown"].append(demo_stat)
            
            logger.info(f"Demo {i} statistics:")
            logger.info(f"   Success: {result['query_success']}")
            logger.info(f"   Tables used: {len(result['relevant_schemas'])}")
            logger.info(f"   Data records: {len(result['data']) if result['query_success'] else 0}")
            logger.info(f"   Execution time: {demo_time:.2f}s")
            if result.get('performance'):
                perf = result['performance']
                logger.info(f"   Retrieval: {perf.get('retrieval_time', 0):.2f}s")
                logger.info(f"   SQL Generation: {perf.get('sql_generation_time', 0):.2f}s") 
                logger.info(f"   Query Execution: {perf.get('execution_time', 0):.2f}s")
                logger.info(f"   Answer Generation: {perf.get('answer_generation_time', 0):.2f}s")
            
            print("-" * 80)
            print("Analysis Results:")
            print("-" * 80)
            print(f"AI identified relevant tables: {', '.join(result['relevant_schemas'])}")
            print(f"Tables involved: {len(result['relevant_schemas'])}")
            print(f"\nGenerated SQL query:")
            print(f"```sql")
            print(result['sql_query'])
            print(f"```")
            
            if result['query_success']:
                print(f"\nQuery executed successfully, returned {len(result['data'])} results")
                print(f"\nAI Analysis:")
                print("=" * 50)
                print(result['answer'])
                print("=" * 50)
                
                if result['data']:
                    print(f"\nKey Data Summary ({len(result['data'])} records):")
                    for idx, record in enumerate(result['data'][:5], 1):
                        print(f"  {idx}. {record}")
                    if len(result['data']) > 5:
                        print(f"  ... and {len(result['data']) - 5} more records")
            else:
                print(f"\nQuery execution encountered challenges: {result.get('query_error', result.get('answer', 'Unknown error'))}")
                print("This type of complex query needs further optimization of SQL generation strategy")
            
            print("=" * 90)
            if i < len(demo_questions):
                print("Preparing next challenge... (2s)")
                import time
                time.sleep(2)
        
        # 最终统计
        total_demo_time = time.time() - total_start_time
        logger.info("=" * 30)
        logger.info("Enterprise demo final statistics")
        logger.info("=" * 30)
        logger.info(f"Total questions: {demo_stats['total_questions']}")
        logger.info(f"Successful queries: {demo_stats['successful_queries']}")
        logger.info(f"Failed queries: {demo_stats['failed_queries']}")
        if demo_stats.get('schema_insufficient_queries', 0) > 0:
            logger.info(f"DDL insufficient rejections: {demo_stats['schema_insufficient_queries']}")
        logger.info(f"Success rate: {demo_stats['successful_queries']/demo_stats['total_questions']*100:.1f}%")
        logger.info(f"Total tables involved: {len(demo_stats['total_tables_used'])}")
        logger.info(f"Tables used: {sorted(list(demo_stats['total_tables_used']))}")
        logger.info(f"Total demo time: {total_demo_time:.2f}s")
        logger.info(f"Average time per question: {total_demo_time/demo_stats['total_questions']:.2f}s")
        logger.info("Average performance metrics:")
        logger.info(f"   Retrieval: {sum(stat['performance'].get('retrieval_time', 0) for stat in demo_stats['performance_breakdown'])/demo_stats['total_questions']:.2f}s")
        logger.info(f"   SQL Generation: {sum(stat['performance'].get('sql_generation_time', 0) for stat in demo_stats['performance_breakdown'])/demo_stats['total_questions']:.2f}s")
        logger.info(f"   Query Execution: {sum(stat['performance'].get('execution_time', 0) for stat in demo_stats['performance_breakdown'])/demo_stats['total_questions']:.2f}s")
        logger.info(f"   Answer Generation: {sum(stat['performance'].get('answer_generation_time', 0) for stat in demo_stats['performance_breakdown'])/demo_stats['total_questions']:.2f}s")
        logger.info("=" * 30)
        
        print("\n" + "=" * 60)
        print("Enterprise Complex Multi-table Query Demo Completed!")
        print("=" * 60)
        
        print("\nAI demonstrated powerful capabilities in enterprise data analysis:")
        print("   ✓ Intelligent association analysis of 10 core business tables")
        print("   ✓ Automatic SQL generation for complex business logic")
        print("   ✓ Multi-dimensional data aggregation and deep insights")
        print("   ✓ Full-stack capability from simple queries to complex analysis")
        print("   ✓ Precise understanding and processing of Chinese business scenarios")
        
        print(f"\nTechnical Achievement Statistics:")
        print(f"   Demo query count: {demo_stats['total_questions']} complex scenarios")
        print(f"   Query success rate: {demo_stats['successful_queries']}/{demo_stats['total_questions']} ({demo_stats['successful_queries']/demo_stats['total_questions']*100:.1f}%)")
        print(f"   Data tables involved: {len(demo_stats['total_tables_used'])} enterprise core tables")
        print(f"   Average table associations: {sum(len(stat['table_names']) for stat in demo_stats['performance_breakdown'])/demo_stats['total_questions']:.1f} tables/query")
        print(f"   AI capability demonstration: Vector retrieval + SQL generation + Natural language understanding")
        print(f"   Total time: {total_demo_time:.1f}s (average {total_demo_time/demo_stats['total_questions']:.1f}s/question)")
        
        print("\nThis is the real power of next-generation enterprise Chinese NL2SQL systems!")

    except (ValueError, ImportError) as e:
        print(f"\n❌ 设置过程中发生错误: {e}")
    except Exception as e:
        logger.error("An unexpected error occurred during the demo.", exc_info=True)
        print(f"\n❌ 发生意外错误: {e}")

if __name__ == "__main__":
    run_demo()