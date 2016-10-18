from neo4j.v1 import GraphDatabase, basic_auth
import requests
import json

driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("",""), encrypted=False)
session = driver.session()

with open('credentials.json') as f:
    credentials = json.loads(f.read())

client_id = credentials["client_id"]
client_secret = credentials["client_secret"]

repository = "PrestaShop/PrestaShop"
contents_url = "https://api.github.com/repos/" + repository + "/contents/"

def getDirectoryContent(path):
    url = contents_url + path
    response = requests.get(url)

    return response.text

def traverse(currentDir):
    files = []
    contents = json.loads(getDirectoryContent(currentDir+"?client_id=" + client_id + "&client_secret=" + client_secret))
    for elt in contents:
        if elt["type"] == "dir":
            traverse(elt["path"])
        elif elt["type"] == "file":
          files.append(elt["path"])

    q = '''UNWIND {files} AS file
            WITH split(file,"/") AS elts
            WITH elts WHERE size(elts) > 1
            UNWIND range(0,size(elts)-1) AS i
            MERGE (prev:File {path: reduce(s="",x IN range(0,i-2) | s+ elts[x]+"/") + CASE i WHEN 0 THEN "" ELSE elts[i-1] END})
            SET prev.name = CASE i WHEN 0 THEN "." ELSE elts[i-1] END
            MERGE (file:File {path: reduce(s="",x IN range(0,i-1) | s+ elts[x]+"/") + elts[i]})
            SET file.name = elts[i]
            MERGE (file)-[:PARENT]->(prev)
            WITH reduce(s="",x IN range(0,size(elts)-2) | s+ elts[x]+"/") + elts[-1] AS la
            MATCH (f:File {path:la})
            SET f:FileRecord'''
    session.run(q, {"files": files})
    print(currentDir)


currentDir = "."
traverse(currentDir)

