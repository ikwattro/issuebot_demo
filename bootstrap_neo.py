from neo4j.v1 import GraphDatabase, basic_auth

driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("",""), encrypted=False)
session = driver.session()

session.run("CREATE CONSTRAINT ON (f:File) ASSERT f.path IS UNIQUE;").consume()
