"""
services/storage.py

Storage layer for the Generative AI RAG System.

This module defines the storage architecture for managing **project data**, **PDF metadata**, 
and **chunk embeddings** across two databases:

1. Neo4j Graph Database — stores project, PDF, and chunk relationships as nodes and edges.
   - Each project is represented as a `Project` node.
   - Each PDF is a `PDF` node connected to its project via `HAS_PDF`.
   - Each text chunk (with embeddings) is a `Chunk` node linked to its PDF via `HAS_CHUNK`.
   - A vector index on `Chunk.embedding` enables efficient semantic search.

2. MongoDB — stores metadata documents for quick lookup and retrieval of project and PDF information.
   - Useful for storing high-level metadata, logs, or analytics separate from the Neo4j graph.

The module provides two main classes:

- BaseStorage (abstract)
  Defines the standard storage interface (`ensure_index`, `store_project`, `close`) 
  that all storage backends should implement.

- Neo4jStorage (BaseStorage)
  Implements storage for graph-based project structures, PDF nodes, and chunk embeddings.
  Handles Neo4j connection setup, index creation, and node/relationship persistence.

- MongoMetadata
  Provides a lightweight MongoDB client for storing and retrieving project or PDF metadata.

Key Functionalities:

- Connects to Neo4j and MongoDB using environment variables (`.env` file).
- Ensures Neo4j vector index for embeddings (cosine similarity, 768 dimensions).
- Persists project hierarchy and chunk embeddings to Neo4j.
- Persists metadata to MongoDB.
- Includes robust logging for connection management, insertion, and error handling.
- Supports IST (Asia/Kolkata) timezone for timestamps.
"""

import os
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from neo4j import GraphDatabase
from pymongo import MongoClient
from dotenv import load_dotenv
import pytz

#logging configuration
logger= logging.getLogger(__name__)

#Environment set-up
load_dotenv()

ist= pytz.timezone("Asia/Kolkata")

#base abstract class
class BaseStorage(ABC):
    """
    Abstract base class defining storage operations for chunk and project data. 
    """
    @abstractmethod
    def ensure_index(self):
        """Ensure that required indexs or constraint exists."""
        pass

    @abstractmethod
    def store_project(self, project_name: str, pdf_data: list, chunks: list):
        """
        Store a project with PDFs and chunks.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close all connections.
        """
        pass

#neo4j
class Neo4jStorage(BaseStorage):
    """
    this class is used for project graph, pdfs, chunks in Neo4j.
    ensures neo4j index
    """
    def __init__(self):
        self.uri= os.getenv("NEO4J_URI")
        self.user= os.getenv("NEO4J_USER")
        self.password= os.getenv("NEO4J_PASSWORD")
        self.driver= None
        self._connect()

    def _connect(self):
        """
        Establishes connection to Neo4j
        """
        #Neo4j Connection
        try:
            self.driver= GraphDatabase.driver(self.uri, auth= (self.user, self.password))
            logger.info("Connection Established to Neo4j")
        except Exception as e:
            self.driver= None
            logger.error(f"Neo4j Connection Error : {e}")

    #Neo4j Vector Index Initiallization
    def ensure_index(self):
        """
        Checking Neo4j vector index is exists for chunk embedding.
        create a index if not exists.
        """
        if not self.driver:
            logger.warning("Neo4j Driver is not yet started; skipping index creation.")
            return
        
        try:
            with self.driver.session() as session:
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
                    """
                )
                logger.info("Neo4j vector index ensured.")
        except Exception as e:
            logger.error(f"[Neo4j Index Error] {e}")
    
    def store_project(self, project_name: str, pdf_data: list, chunks: list):
        """
        Stores a project, it's PDFs, and their text chunks in Neo4j.
        Ensures vector index is present.
        Arguments:
            project_name ---> str: The name of the project.
            pdf_data ---> list[dict]: List of PDF metadata dictionaries (name, pages),
            chunks ---> list[dict]: List of text chunks dictionaries with embeddings.
        """

        if not self.driver:
            logger.warning("Neo4j Driver is not yet initialized; skipping project storage.")
            return

        try:
            #vector index creation
            self.ensure_index()

            with self.driver.session() as session:
                #project node
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
                logger.info(f"Created or merged Project_node: {project_name}")
                
                #PDF Nodes
                for pdf in pdf_data:

                    pdf_name= pdf.get("name") or pdf.get("pdf_name")
                    pages= pdf.get("pages", 0)

                    if not pdf_name:
                        logger.warning(f"skipping PDF with missing name field: {pdf}")

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
                                "pdf_name": pdf_name, #did here also
                                "pages": pages #here also
                            }
                        )
                        logger.info(f"Stored PDF node: {pdf_name}")
                    except Exception as e:
                        logger.error(f"Neo4j Couldn't Store PDF '{pdf_name}': {e}")

                #chunk nodes
                logger.info(f"starting chunk storage for {len(chunks)} chunks...")
                for c in chunks:
                    pdf_name= c.get("pdf_name")
                    page_num= c.get("page_num")
                    pdf_path= c.get("pdf_path")
                    try:
                        session.run(
                            """
                            MATCH (pdf:PDF {name: $pdf_name})
                            MERGE (chunk:Chunk {pdf_name: $pdf_name, chunk_id: $id})
                            SET chunk.text = $text, 
                                chunk.embedding = $embedding,
                                chunk.page_num = $page_num,
                                chunk.pdf_path = $pdf_path
                            MERGE (pdf)-[:HAS_CHUNK]->(chunk)
                            """,
                            {
                                "pdf_name": pdf_name,
                                "id": c.get("chunk_id"),
                                "text": c.get("text", ""),
                                "embedding": c.get('embedding',[]),
                                "page_num": page_num,
                                "pdf_path": pdf_path
                            }
                        )
                        logger.info(f"Stored chunk {c['chunk_id']} for PDF {pdf_name}")
                    except Exception as e:
                        logger.error(f"Neo4j Chunk Error, PDF '{pdf_name}' Chunk_ID {c.get('chunk_id')}: {e}")

            logger.info(f"Neo4j Project {project_name}, stored successfully")
        
        except Exception as e:
            logger.error(f"Neo4j Storage Error: {e}")
    
    #neo4j connection close
    def close(self):
        """
        Close active Neo4j and MongoDB connections.
        """
        try:
            if self.driver:
                self.driver.close()
                logger.info("Neo4j Connection Closed")
        except Exception as e:
            logger.error(f"Neo4j Connection Close error: {e}")


#mongodb metadata storage
class MongoMetadata:
    """
    sotres metadata in mongodb for pdf and project info.
    """

    def __init__(self):

        #mongodb credentials
        self.url= os.getenv("MONGODB_URI")
        self.db= os.getenv("MONGODB_DB")
        self.collection_name= os.getenv("MONGODB_COLLECTION")
        self.client= None
        self.collection= None
        self._connect()

    def _connect(self):
        """
        Establish a MongDB client Connection.
        """
        #MongoDB Connection
        try:
            if not self.url:
                raise ValueError("Missing MongoDB URI in .env file.")
            client= MongoClient(self.url)
            self.client= client

            if self.db is None or self.collection_name is None:
                raise ValueError("Missing MongoDB or MongoDB Collection in .env file.")
            self.collection= client[self.db][self.collection_name]
            logger.info("Connection Established to MongoDB")
        except Exception as e:
            logger.error(f"MongoDB Connection error: {e}")
            self.client= None
            self.collection= None

    #store metadata in MongoDB
    def store_metadata(self,metadata: dict):
        """
        Stores PDF metadata into MongoDB.

        Arguments:
            meatadata---> dict: Meatadata dictionary containing project and PDF Info.
        """
        if self.collection is None:
            logger.warning("MongDB not initialised; skipping metadata storage.")
            return

        try:
            self.collection.insert_one(metadata)
            logger.info(f"MongoDB Metadata stored for PDF: {metadata.get('pdf_name')}")
        except Exception as e:
            logger.error(f"MongoDB Couldn't store metadata: {e}")

    def close(self):
        #close connection
        try:
            if self.client is not None:
                self.client.close()
                logger.info(f"MongDB Connection Closed")
        except Exception as e:
            logger.error(f"MongoDB Connection Close Error: {e}")