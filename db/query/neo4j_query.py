import re
from typing import (
    Type, Dict, Any, List, Optional, Callable, TypeVar, Union
)
from pydantic import BaseModel
from neo4j import GraphDatabase, Driver, Record, Session

T = TypeVar('T', bound=BaseModel)


class GenericNeo4jQuery:
    """
    通用 Neo4j 客户端，支持任意 Pydantic 模型。
    要求模型定义：
      - __label__: ClassVar[str] （节点标签）
      - 字段可通过 Field(..., unique=True) 标记为唯一键（用于 MERGE）
    """

    def __init__(self, driver: Driver):
        self.driver = driver

    @staticmethod
    def _validate_identifier(name: str) -> bool:
        """校验标签/关系类型是否合法（防注入）"""
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))

    def _extract_node_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """从 Pydantic 模型提取节点元数据"""
        label = getattr(model, "__label__", model.__name__)
        if not self._validate_identifier(label):
            raise ValueError(f"Invalid label: {label}")

        fields = model.model_fields
        all_props = list(fields.keys())
        merge_keys = [
            k for k, v in fields.items()
            if v.json_schema_extra and v.json_schema_extra.get("unique")
        ]
        return {"label": label, "all_props": all_props, "merge_keys": merge_keys}

    def _extract_rel_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """从 Pydantic 模型提取关系元数据"""
        rel_type = getattr(model, "__rel_type__", model.__name__.upper())
        if not self._validate_identifier(rel_type):
            raise ValueError(f"Invalid relationship type: {rel_type}")
        fields = model.model_fields
        all_props = list(fields.keys())
        return {"rel_type": rel_type, "all_props": all_props}

    def _model_to_dict(self, obj: BaseModel) -> Dict[str, Any]:
        return obj.model_dump(exclude_none=True)

    def _node_to_model(self, node, model_class: Type[T]) -> T:
        data = dict(node.items())
        return model_class(**data)

    def _record_to_model(self, record: Record, model_class: Type[T]) -> T:
        """将 Neo4j Record 转为 Pydantic 模型（支持嵌套 Node/Relationship）"""
        data = {}
        for field_name, field_info in model_class.model_fields.items():
            if field_name in record:
                value = record[field_name]
                if hasattr(value, 'items'):
                    data[field_name] = dict(value.items())
                else:
                    data[field_name] = value
            else:
                data[field_name] = record.get(field_name)
        return model_class(**data)

    def create_node(self, obj: BaseModel) -> BaseModel:
        schema = self._extract_node_schema(type(obj))
        props = self._model_to_dict(obj)
        cypher = f"CREATE (n:{schema['label']}) SET n = $props RETURN n"
        with self.driver.session() as session:
            result = session.run(cypher, props=props)
            return self._node_to_model(result.single()["n"], type(obj))

    def merge_node(self, obj: BaseModel) -> BaseModel:
        schema = self._extract_node_schema(type(obj))
        if not schema["merge_keys"]:
            raise ValueError(f"No 'unique=True' field in {obj.__class__.__name__}")

        props = self._model_to_dict(obj)
        merge_props = {k: props[k] for k in schema["merge_keys"] if k in props}
        other_props = {k: v for k, v in props.items() if k not in schema["merge_keys"]}

        merge_clause = ", ".join([f"{k}: ${k}" for k in merge_props.keys()])
        cypher = f"""
        MERGE (n:{schema['label']} {{{merge_clause}}})
        ON CREATE SET n += $other_props
        ON MATCH SET n += $other_props
        RETURN n
        """
        params = {**merge_props, "other_props": other_props}

        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return self._node_to_model(result.single()["n"], type(obj))

    def find_nodes(
            self,
            model_class: Type[BaseModel],
            match_props: Optional[Dict[str, Any]] = None
    ) -> List[BaseModel]:
        schema = self._extract_node_schema(model_class)
        if match_props:
            where_clause = " AND ".join([f"n.{k} = ${k}" for k in match_props.keys()])
            cypher = f"MATCH (n:{schema['label']}) WHERE {where_clause} RETURN n"
        else:
            cypher = f"MATCH (n:{schema['label']}) RETURN n"

        with self.driver.session() as session:
            results = session.run(cypher, **(match_props or {}))
            return [self._node_to_model(record["n"], model_class) for record in results]

    def update_nodes(
            self,
            model_class: Type[BaseModel],
            set_props: Dict[str, Any],
            match_props: Dict[str, Any]
    ) -> int:
        if not match_props:
            raise ValueError("match_props must be provided for update")
        schema = self._extract_node_schema(model_class)
        set_clause = ", ".join([f"n.{k} = ${k}" for k in set_props.keys()])
        where_clause = " AND ".join([f"n.{k} = ${k}" for k in match_props.keys()])
        cypher = f"MATCH (n:{schema['label']}) WHERE {where_clause} SET {set_clause} RETURN count(n) AS count"

        params = {**match_props, **set_props}
        with self.driver.session() as session:
            result = session.run(cypher, **params)
            return result.single()["count"]

    def delete_nodes(
            self,
            model_class: Type[BaseModel],
            match_props: Dict[str, Any]
    ) -> int:
        if not match_props:
            raise ValueError("match_props must be provided for delete")
        schema = self._extract_node_schema(model_class)
        where_clause = " AND ".join([f"n.{k} = ${k}" for k in match_props.keys()])
        cypher = f"MATCH (n:{schema['label']}) WHERE {where_clause} DETACH DELETE n RETURN count(n) AS count"

        with self.driver.session() as session:
            result = session.run(cypher, **match_props)
            return result.single()["count"]

    def create_relationship(
            self,
            from_obj: BaseModel,
            to_obj: BaseModel,
            rel_obj: BaseModel
    ) -> BaseModel:
        from_schema = self._extract_node_schema(type(from_obj))
        to_schema = self._extract_node_schema(type(to_obj))
        rel_schema = self._extract_rel_schema(type(rel_obj))

        from_merge = {k: getattr(from_obj, k) for k in from_schema["merge_keys"]}
        to_merge = {k: getattr(to_obj, k) for k in to_schema["merge_keys"]}
        if not from_merge or not to_merge:
            raise ValueError("Source and target nodes must have unique fields")

        rel_props = self._model_to_dict(rel_obj)
        from_match = ", ".join([f"a.{k} = ${'from_' + k}" for k in from_merge.keys()])
        to_match = ", ".join([f"b.{k} = ${'to_' + k}" for k in to_merge.keys()])

        cypher = f"""
        MATCH (a:{from_schema['label']}), (b:{to_schema['label']})
        WHERE {from_match} AND {to_match}
        CREATE (a)-[r:{rel_schema['rel_type']}]->(b)
        SET r = $rel_props
        RETURN r
        """
        params = {
            **{f"from_{k}": v for k, v in from_merge.items()},
            **{f"to_{k}": v for k, v in to_merge.items()},
            "rel_props": rel_props
        }

        with self.driver.session() as session:
            result = session.run(cypher, **params)
            if not result.single():
                raise ValueError("Source or target node not found")
            return rel_obj

    def batch_merge_nodes(self, objects: List[BaseModel]) -> List[BaseModel]:
        if not objects:
            return []
        model_class = type(objects[0])
        schema = self._extract_node_schema(model_class)
        if not schema["merge_keys"]:
            raise ValueError("Batch merge requires unique fields")

        def _batch_tx(tx):
            results = []
            for obj in objects:
                props = self._model_to_dict(obj)
                merge_props = {k: props[k] for k in schema["merge_keys"] if k in props}
                other_props = {k: v for k, v in props.items() if k not in schema["merge_keys"]}
                merge_clause = ", ".join([f"{k}: ${k}" for k in merge_props.keys()])
                cypher = f"""
                MERGE (n:{schema['label']} {{{merge_clause}}})
                ON CREATE SET n += $other_props
                ON MATCH SET n += $other_props
                RETURN n
                """
                params = {**merge_props, "other_props": other_props}
                result = tx.run(cypher, **params)
                node = result.single()["n"]
                results.append(self._node_to_model(node, model_class))
            return results

        with self.driver.session() as session:
            return session.execute_write(_batch_tx)

    def batch_create_relationships(
            self,
            rel_data: List[tuple[BaseModel, BaseModel, BaseModel]]
    ) -> List[BaseModel]:
        if not rel_data:
            return []

        def _batch_rel_tx(tx):
            results = []
            for from_obj, to_obj, rel_obj in rel_data:
                from_schema = self._extract_node_schema(type(from_obj))
                to_schema = self._extract_node_schema(type(to_obj))
                rel_schema = self._extract_rel_schema(type(rel_obj))

                from_merge = {k: getattr(from_obj, k) for k in from_schema["merge_keys"]}
                to_merge = {k: getattr(to_obj, k) for k in to_schema["merge_keys"]}
                rel_props = self._model_to_dict(rel_obj)

                from_match = ", ".join([f"a.{k} = ${'from_' + k}" for k in from_merge.keys()])
                to_match = ", ".join([f"b.{k} = ${'to_' + k}" for k in to_merge.keys()])

                cypher = f"""
                MATCH (a:{from_schema['label']}), (b:{to_schema['label']})
                WHERE {from_match} AND {to_match}
                CREATE (a)-[r:{rel_schema['rel_type']}]->(b)
                SET r = $rel_props
                RETURN r
                """
                params = {
                    **{f"from_{k}": v for k, v in from_merge.items()},
                    **{f"to_{k}": v for k, v in to_merge.items()},
                    "rel_props": rel_props
                }
                tx.run(cypher, **params)
                results.append(rel_obj)
            return results

        with self.driver.session() as session:
            return session.execute_write(_batch_rel_tx)

    def query(
            self,
            cypher: str,
            parameters: Optional[Dict[str, Any]] = None,
            result_transformer: Optional[Callable[[Record], T]] = None,
            model_class: Optional[Type[T]] = None
    ) -> list[T] | List[Dict]:
        if parameters is None:
            parameters = {}
        with self.driver.session() as session:
            results = session.run(cypher, **parameters)
            if result_transformer:
                return [result_transformer(record) for record in results]
            elif model_class:
                return [self._record_to_model(record, model_class) for record in results]
            else:
                return [dict(record) for record in results]

    def paginate(
            self,
            model_class: Type[BaseModel],
            match_conditions: Optional[Dict[str, Any]] = None,
            order_by: str = "id(n)",
            ascending: bool = True,
            page: int = 1,
            size: int = 10
    ) -> List[BaseModel]:
        if page < 1 or size < 1:
            raise ValueError("page and size must be positive integers")

        schema = self._extract_node_schema(model_class)
        skip = (page - 1) * size
        direction = "ASC" if ascending else "DESC"

        where_clause = ""
        params = {}
        if match_conditions:
            where_clause = "WHERE " + " AND ".join([f"n.{k} = ${k}" for k in match_conditions.keys()])
            params.update(match_conditions)

        cypher = f"""
        MATCH (n:{schema['label']})
        {where_clause}
        RETURN n
        ORDER BY {order_by} {direction}
        SKIP $skip
        LIMIT $limit
        """
        params.update({"skip": skip, "limit": size})

        return self.query(cypher, params, model_class=model_class)
