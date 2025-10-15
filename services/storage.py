from neo4j import GraphDatabase
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()

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
ist= pytz.timezone("Asia/Kolkata")

def ensure_vector_index():
    try:
        with driver.session() as session:
            session.run(
            """
            CREATE VECTOR INDEX vector_index IF NOT EXISTS
            FOR (c:Chunk)
            ON (c.embedding)
            OPTIONS {
            indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: 'cosine'
            }
            };
            """)
            print("Neo4j vector index ensured.")
    except Exception as e:
        print(f"[Neo4j Index Error] {e}")

def store_project_graph(project_name, pdf_data, chunks):
    with driver.session() as session:
        session.run(
            """
            MERGE (p: Project {name: $name})
            ON CREATE SET p.date_created= $date
            """,
            {
                "name": project_name,
                "date": datetime.now(ist).isoformat()
            }
        )
        for pdf in pdf_data:
            session.run(
                """
                MATCH (p: Project {name: $project_name})
                MERGE (pdf: PDF {name: $pdf_name})
                SET pdf.pages= $pages
                MERGE (p)-[:HAS_PDF]->(pdf)
                """,
                {
                    "project_name": project_name,
                    "pdf_name": pdf['name'],
                    "pages": pdf['pages']
                }
            )
        for c in chunks:
            pdf_name= c.get("pdf_name", pdf_data[0]["name"])
            session.run(
                """
                MATCH (pdf:PDF {name: $pdf_name})
                MERGE (chunk:Chunk {chunk_id: $id})
                SET chunk.text = $text, 
                    chunk.embedding = $embedding
                MERGE (pdf)-[:HAS_CHUNK]->(chunk)
                """,
                {
                    "pdf_name": pdf_name,
                    "id": c["chunk_id"],
                    "text": c["text"],
                    "embedding": c['embedding']
                }
            )
def store_metadata(metadata):
    mongo.insert_one(metadata)

def close_connection():
    driver.close()
    mongo.database.client.close()