from neo4j import GraphDatabase
from pymongo import MongoClient
import os
from dotenv import load_dotenv

#neo4j
uri= os.getenv("NEO4J_URI")
user= os.getenv("NEO4J_USER")
password= os.getenv("NEO4J_PASSWORD")

#mongodb
url= os.getenv("MONGODB_URI")
db= os.getenv("MONGODB_DB")
collection= os.getenv("MONGODB_COLLECTION")

driver= GraphDatabase.driver(uri, auth= (user, password))
mongo= MongoClient(url)[db][collection]

def store_project_graph(project_name, pdf_data, chunks):
    with driver.session() as session:
        session.run(
            "CREATE (p: Project {name: $name, date_created: $date})"
            name= project_name,
            date= datetime.utcnow().isoformat()
        )
        for pdf in pdf_data:
            session.run(
                """
                MATCH (p: Project {name: $project_name})
                CREATE (pdf: PDF {name: $pdf_name, pages: $pages})
                CREATE (p)-[:HAS_PDF]->(pdf)
                """,
                project_name= project_name,
                pdf_name= pdf['name'],
                pages= pdf['pages']
            )
        for c in chunks:
            session.run(
                """
                MATCH (pdf:PDF {name: $pdf_name})
                CREATE (c:Chunk {chunk_id: $id, text: $text, embedding: $embedding})
                CREATE (pdf)-[:HAS_CHUNKS]->(c)
                """,
                pdf_name= pdf_data[0]['name'],
                id= c["chunk_id"],
                text= c["text"],
                embeddings= c['embedding']
            )
def store_metadata(metadata):
    mongo.insert_one(metadata)