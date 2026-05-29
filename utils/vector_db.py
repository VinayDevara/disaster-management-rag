"""
Vector Database Manager using ChromaDB
Handles embedding storage and similarity search for RAG
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Any
from config.config import Config
import uuid

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
            # Map columns cleanly
            flight = record.get('flight') or record.get('aircraft__flight') or 'Unknown'
            hex_code = record.get('hex') or record.get('aircraft__hex') or 'N/A'
            alt_baro = record.get('alt_baro') or record.get('aircraft__alt_baro') or 'N/A'
            gs = record.get('gs') or record.get('aircraft__gs') or 'N/A'
            lat = record.get('lat') or record.get('aircraft__lat') or 'N/A'
            lon = record.get('lon') or record.get('aircraft__lon') or 'N/A'
            squawk = record.get('squawk') or record.get('aircraft__squawk') or 'N/A'
            category = record.get('category') or record.get('aircraft__category') or 'N/A'
            emergency = record.get('emergency') or record.get('aircraft__emergency') or 'none'
            timestamp = record.get('timestamp') or record.get('now') or ''
            
            # Create text representation
            text = f"""Flight {flight} 
Aircraft Hex: {hex_code}
Altitude: {alt_baro} ft
Ground Speed: {gs} knots
Position: {lat}, {lon}
Squawk: {squawk}
Category: {category}
Emergency: {emergency}
"""
            documents.append(text)
            
            # Store metadata
            metadatas.append({
                "hex": str(hex_code),
                "flight": str(flight),
                "timestamp": str(timestamp),
                "lat": float(lat) if lat != 'N/A' else 0.0,
                "lon": float(lon) if lon != 'N/A' else 0.0,
                "emergency": str(emergency)
            })
            
            ids.append(f"flight_{hex_code}_{timestamp}")
        
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