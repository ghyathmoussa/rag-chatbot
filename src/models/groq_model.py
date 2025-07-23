import time
from typing import List, Optional, Dict, Any
from groq import Groq
from src.configs.configs import GROQ_API_KEY, GROQ_MODEL
from src.models.embedding_model import Embedder
from src.models.qdrant_model import QDrantModel
from src.database.conversation_service import conversation_service
from src.utils.logger import logger
from langchain.document_loaders import TextLoader
class GroqModel:
    def __init__(self, conversation_id: Optional[int] = None):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.embedder = Embedder()
        self.store = QDrantModel()
        self.conversation_id = conversation_id
        self.system_prompt = "You are a helpful AI assistant that uses the provided context to answer questions accurately."
    
    def grqo_chat(self, user_query: str, context: List[str]) -> str:
        """Chat with context and save to database"""
        start_time = time.time()
        
        try:
            # Format context
            formatted_context = "\n\n".join(context) if context else "No context available."
            
            # Create messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{formatted_context}\n\nQuestion: {user_query}"}
            ]
            
            # Get response from Groq
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            assistant_response = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            # Save to database if conversation exists
            if self.conversation_id:
                # Save user message
                conversation_service.add_message(
                    conversation_id=self.conversation_id,
                    role="user",
                    content=user_query,
                    metadata={"has_context": bool(context)}
                )
                
                # Save assistant response
                conversation_service.add_message(
                    conversation_id=self.conversation_id,
                    role="assistant",
                    content=assistant_response,
                    context_used=context,
                    model_used=GROQ_MODEL,
                    processing_time=processing_time,
                    token_count=response.usage.total_tokens if hasattr(response, 'usage') else None
                )
            
            logger.info(f"Generated response in {processing_time:.2f}s")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error in grqo_chat: {e}")
            return "Sorry, I encountered an error while processing your request."

    def process_and_store(self, file_path: str):
        """Process document and store embeddings"""
        try:
            # Load document
            loader = TextLoader(file_path)
            documents = loader.load()
            
            # Extract text
            text = "\n".join([doc.page_content for doc in documents])
            
            # Chunk and embed
            chunks = self.embedder.chunk_text(text)
            embeddings = self.embedder.embed_chunks(chunks)
            
            # Store in Qdrant
            self.store.store(embeddings, chunks)
            
            logger.info(f"Processed and stored {len(chunks)} chunks from {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    def query_with_context(self, query: str, top_k: int = 5) -> str:
        """Query with RAG context"""
        try:
            # Get query embedding
            query_embedding = self.embedder.embed_chunks([query])[0]
            
            # Search for similar chunks
            results = self.store.query(query_embedding, top_k=top_k)
            
            # Extract context
            context = [result["text"] for result in results]
            
            # Generate response
            return self.grqo_chat(query, context)
            
        except Exception as e:
            logger.error(f"Error in query_with_context: {e}")
            return "Sorry, I couldn't retrieve relevant context for your question."