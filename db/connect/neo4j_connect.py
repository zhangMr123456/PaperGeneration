from neo4j import GraphDatabase

from conf.settings import NEO4J_USER_DATABASE

# URI examples: "db://localhost", "db+s://xxx.databases.db.io"
auth = (NEO4J_USER_DATABASE["username"], NEO4J_USER_DATABASE["password"])
with GraphDatabase.driver(NEO4J_USER_DATABASE["uri"], auth=auth) as driver:
    driver.verify_connectivity()
    print("Connection established.")