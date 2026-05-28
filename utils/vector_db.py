"""
Vector Database Manager using ChromaDB
Handles embedding storage and similarity search for RAG
"""
import os

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
from config.config import Config
import uuid

def _first_value(record: Dict, *keys):
    """Return the first non-empty value for the given keys."""
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None
class VectorDBManager:
    """
    Vector database manager for semantic search
    Optimized for low-resource environments
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or Config.VECTOR_DB_PATH
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        print(f"🔄 Loading embedding model: {Config.EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        print("✅ Embedding model loaded")
        
        # Create collections
        self.collections = self._initialize_collections()
    
    def _initialize_collections(self) -> Dict[str, Any]:
        """Initialize vector collections for different data types"""
        collections = {}
        
        # Flight data collection
        collections['flights'] = self.client.get_or_create_collection(
            name="flights",
            metadata={"description": "ADS-B flight tracking data"}
        )
        
        # Weather events collection
        collections['weather'] = self.client.get_or_create_collection(
            name="weather",
            metadata={"description": "Weather events and conditions"}
        )
        
        # Disaster events collection
        collections['disasters'] = self.client.get_or_create_collection(
            name="disasters",
            metadata={"description": "Natural disaster events"}
        )
        
        # Knowledge base collection (general info)
        collections['knowledge'] = self.client.get_or_create_collection(
            name="knowledge",
            metadata={"description": "General disaster management knowledge"}
        )
        
        print(f"✅ Initialized {len(collections)} vector collections")
        return collections
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to vector collection
        
        Args:
            collection_name: Name of collection
            documents: List of text documents
            metadatas: Optional metadata for each document
            ids: Optional custom IDs (generated if not provided)
        """
        if collection_name not in self.collections:
            print(f"❌ Collection '{collection_name}' not found")
            return
        
        collection = self.collections[collection_name]
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate embeddings
        embeddings = [self.generate_embedding(doc) for doc in documents]
        
        # Add to collection
        try:
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas or [{} for _ in documents],
                ids=ids
            )
            print(f"✅ Added {len(documents)} documents to '{collection_name}' collection")
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
    
    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents
        
        Args:
            collection_name: Name of collection to search
            query: Search query text
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Search results with documents, distances, and metadata
        """
        if collection_name not in self.collections:
            print(f"❌ Collection '{collection_name}' not found")
            return {"documents": [], "metadatas": [], "distances": []}
        
        collection = self.collections[collection_name]
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    def add_flight_data(self, flight_records: List[Dict]):
        """
        Add flight data to vector database
        
        Args:
            flight_records: List of flight dictionaries
        """
        documents = []
        metadatas = []
        ids = []
        
        for record in flight_records:
            flight = _first_value(record, "flight", "aircraft__flight")
            hex_code = _first_value(record, "hex", "aircraft__hex")
            alt_baro = _first_value(record, "alt_baro", "aircraft__alt_baro")
            gs = _first_value(record, "gs", "aircraft__gs")
            lat = _first_value(record, "lat", "aircraft__lat")
            lon = _first_value(record, "lon", "aircraft__lon")
            squawk = _first_value(record, "squawk", "aircraft__squawk")
            category = _first_value(record, "category", "aircraft__category")
            emergency = _first_value(record, "emergency", "aircraft__emergency")
            timestamp = _first_value(record, "timestamp", "now")

            # Create text representation
            text = f"""Flight {flight or 'Unknown'}
Aircraft Hex: {hex_code or 'N/A'}
Altitude: {alt_baro or 'N/A'} ft
Ground Speed: {gs or 'N/A'} knots
Position: {lat or 'N/A'}, {lon or 'N/A'}
Squawk: {squawk or 'N/A'}
Category: {category or 'N/A'}
Emergency: {emergency or 'none'}
"""
            documents.append(text)
            
            # Store metadata
            metadatas.append({
                "hex": str(hex_code or ""),
                "flight": str(flight or ""),
                "timestamp": str(timestamp or ""),
                "lat": float(lat) if lat else 0,
                "lon": float(lon) if lon else 0,
                "emergency": str(emergency or "none")
            })
            
            ids.append(f"flight_{hex_code or uuid.uuid4()}_{timestamp or ''}")
        
        self.add_documents('flights', documents, metadatas, ids)

    def add_weather_event(self, event: Dict):
        """Add weather event to vector database"""
        text = f"""Weather Event: {event.get('event_type', 'Unknown')}
Title: {event.get('title', '')}
Description: {event.get('description', '')}
Location: {event.get('location_name', 'Unknown')}
Coordinates: {event.get('lat', 'N/A')}, {event.get('lon', 'N/A')}
Severity: {event.get('severity', 'Unknown')}
Time: {event.get('start_time', 'Unknown')}
"""
        
        metadata = {
            "event_id": str(event.get('event_id', '')),
            "event_type": str(event.get('event_type', '')),
            "lat": float(event.get('lat', 0)) if event.get('lat') else 0,
            "lon": float(event.get('lon', 0)) if event.get('lon') else 0,
            "severity": str(event.get('severity', 'unknown'))
        }
        
        self.add_documents('weather', [text], [metadata], [event.get('event_id', str(uuid.uuid4()))])
    
    def add_disaster_event(self, event: Dict):
        """Add disaster event to vector database"""
        text = f"""Disaster Event: {event.get('title', 'Unknown')}
Type: {event.get('event_type', 'Unknown')}
Description: {event.get('description', '')}
Location: {event.get('location_name', 'Unknown')}
Coordinates: {event.get('lat', 'N/A')}, {event.get('lon', 'N/A')}
Start Date: {event.get('start_date', 'Unknown')}
Severity: {event.get('severity', 'Unknown')}
"""
        
        metadata = {
            "event_id": str(event.get('event_id', '')),
            "event_type": str(event.get('event_type', '')),
            "lat": float(event.get('lat', 0)) if event.get('lat') else 0,
            "lon": float(event.get('lon', 0)) if event.get('lon') else 0,
            "severity": str(event.get('severity', 'unknown'))
        }
        
        self.add_documents('disasters', [text], [metadata], [event.get('event_id', str(uuid.uuid4()))])
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get number of documents in collection"""
        if collection_name not in self.collections:
            return 0
        return self.collections[collection_name].count()
    
    def reset_collection(self, collection_name: str):
        """Reset/clear a collection"""
        if collection_name in self.collections:
            self.client.delete_collection(collection_name)
            self.collections[collection_name] = self.client.create_collection(collection_name)
            print(f"✅ Reset collection: {collection_name}")


if __name__ == "__main__":
    # Test vector database
    vector_db = VectorDBManager()
    print("Vector database initialized!")
    
    # Test search
    results = vector_db.search("flights", "emergency landing", n_results=3)
    print(f"Search results: {len(results['documents'])} documents found")