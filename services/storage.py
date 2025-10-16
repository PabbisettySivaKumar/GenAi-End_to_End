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

#Neo4j Connection
try:
    driver= GraphDatabase.driver(uri, auth= (user, password))
    print("Connection Established to Neo4j")
except Exception as e:
    driver= None
    print(f"Neo4j Connection Error : {e}")

#MongoDB Connection
try:
    mongo= MongoClient(url)[db][collection]
except Exception as e:
    mongo= None
    print(f"MongoDB Connection error: {e}")

ist= pytz.timezone("Asia/Kolkata")

#Neo4j Vector Index Initiallization
def ensure_vector_index():

    if not driver:
        print("Neo4j Driver is not yet started")
        return
    
    try:
        with driver.session() as session:
            session.run(
            """
            CREATE VECTOR INDEX vector IF NOT EXISTS
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

    if not driver:
        print("Neo4j Driver is not yet started")
        return

    try:
        #vector index creation
        ensure_vector_index()

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
            #PDF Nodes

            for pdf in pdf_data:
                try:
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
                except Exception as e:
                    print(f"Neo4j Couldn't Store PDF '{pdf['name']}': {e}")

            #chunk nodes        
            for c in chunks:
                pdf_name= c.get("pdf_name")
                try:
                    session.run(
                        """
                        MATCH (pdf:PDF {name: $pdf_name})
                        MERGE (chunk:Chunk {pdf_name: $pdf_name, chunk_id: $id})
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
                except Exception as e:
                    print(f"Neo4j Chunk Error, PDF '{pdf_name}' Chunk_ID {c.get('chunk_id')}: {e}")

        print(f"Neo4j Project {project_name}, stored successfully")
    
    except Exception as e:
        print(f"Neo4j Storage Error: {e}")


def store_metadata(metadata):
    try:      
        mongo.insert_one(metadata)
        print(f"MongoDB Metadata stored for PDF: {metadata.get('pdf_name')}")
    except Exception as e:
        print(f"MongoDB Couldn't store metadata: {e}")


def close_connection():
    try:
        if driver:
            driver.close()
            print("Neo4j Connection Closed")
    except Exception as e:
        print(f"Neo4j Connection Close error: {e}")
    
    try:  
        mongo.database.client.close()
        print(f"MongDB Connection Closed")
    except Exception as e:
        print(f"MongoDB Connection Close Error: {e}")

#Auto vector Index
try:
    ensure_vector_index()
except Exception as e:
    print(f"skipped vextor index creation: {e}")