import nltk
import string
from neo4j.v1 import GraphDatabase, basic_auth
import requests

driver = GraphDatabase.driver("bolt://localhost", auth=basic_auth("",""), encrypted=False)
session = driver.session()

default_tagger = nltk.data.load(nltk.tag._POS_TAGGER)
punctuations = list(string.punctuation)
stemmer = nltk.stem.porter.PorterStemmer()
lemmatizer = nltk.stem.WordNetLemmatizer()
punctuation_map = dict((ord(char), None) for char in string.punctuation)

def stemmer_tokens(tokens):
    return [lemmatizer.lemmatize(stemmer.stem(item)) for item in tokens]

def tokenize_words(s):
    return [i.strip("".join(punctuations)) for i in nltk.word_tokenize(s) if i not in punctuations]

def normalize(text):
    return stemmer_tokens(nltk.word_tokenize(text.lower().translate(punctuation_map)))

pr_template_url = "https://raw.githubusercontent.com/PrestaShop/PrestaShop/develop/.github/PULL_REQUEST_TEMPLATE.md"
response = requests.get(pr_template_url).text
blacklist = normalize(response)

result = session.run('''MATCH (pr:PullRequest)<-[:PR_COMMENT*0..1]-(comment)
RETURN pr.number as number, reduce(text = "", x IN collect(comment) | text + (coalesce(x.title,'') + '.' + x.body + '.')) AS text''')
for record in result:
    text = record["text"]
    number = record["number"]
    pullTags = []

    for tag in normalize(text):
        if len(tag) > 4 and tag not in blacklist:
            pullTags.append(tag)

    q = '''MATCH (pr:PullRequest {number: {number} })
    UNWIND {tags} AS tag
    MERGE (t:Tag {value: toLower(tag) })
    MERGE (t)-[r:TAGS_PR]->(pr) ON MATCH SET r.inc = r.inc + 1 ON CREATE SET r.inc = 1'''

    session.run(q, {"number": number, "tags": pullTags}).consume()
