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
prs_url = "https://api.github.com/repos/" + repository + "/pulls?per_page=100&state=closed&direction=desc&base=develop"
url = prs_url + "&client_id=" + client_id + "&client_secret=" + client_secret

response = requests.get(url)
data = json.loads(response.text)

for pr in data:
    params = {}
    params["number"] = pr["number"]
    params["login"] = pr["user"]["login"]
    params["title"] = pr["title"]
    params["body"] = pr["body"]

    q = '''MERGE (pr:PullRequest {number: {number} })
    ON CREATE SET pr.title = {title}, pr.body = {body}
    MERGE (u:User {login: {login} })
    MERGE (u)-[:CONTRIBUTED_PR]->(pr)'''
    session.run(q, params).consume()

    commentsUrl = "https://api.github.com/repos/" + repository + "/issues/" + str(params["number"]) + "/comments"
    cUrl = commentsUrl + "?client_id=" + client_id + "&client_secret=" + client_secret
    commentsResponse = requests.get(cUrl)

    comments = json.loads(commentsResponse.text)
    for comment in comments:
        params2 = {
            "id": comment["id"],
            "login": comment["user"]["login"],
            "body": comment["body"],
            "prnum": params["number"]
        }
        q = '''MATCH (pr:PullRequest {number: {prnum} })
        MERGE (c:Comment {id: {id} }) SET c.body = {body}
        MERGE (u:User {login: {login} })
        MERGE (u)-[:WROTE_COMMENT]->(c)
        MERGE (c)-[:PR_COMMENT]->(pr)'''
        session.run(q, params2).consume()

    filesUrl = "https://api.github.com/repos/" + repository + "/pulls/" + str(params["number"]) + "/files"
    url = filesUrl + "?client_id=" + client_id + "&client_secret=" + client_secret
    filesResponse = requests.get(url)
    filesData = json.loads(filesResponse.text)

    touchedFiles = []
    for file in filesData:
        touchedFiles.append(file["filename"])

    params3 = {
        "number": params["number"],
        "files": touchedFiles
    }

    q = '''MATCH (pr:PullRequest {number: {number} })
    UNWIND {files} AS file
    MATCH (f:File {path: file})
    MERGE (pr)-[:TOUCHED_FILE]->(f)'''
    session.run(q, params3)
