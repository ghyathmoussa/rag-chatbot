import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from groq import Groq
from src.configs.configs import GROQ_API_KEY, GROQ_MODEL
from src.models.embedding_model import Embedder
from src.models.qdrant_model import QDrantModel
from src.database.conversation_service import conversation_service
from src.database.connection import db_manager
from src.utils.logger import logger

# Document loaders for different file types
from langchain.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, CSVLoader, JSONLoader
class GroqModel:
    def __init__(self, conversation_id: Optional[int] = None):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.embedder = Embedder()
        self.store = QDrantModel(conversation_id=conversation_id)
        self.conversation_id = conversation_id
        self.system_prompt = """You are a helpful AI assistant. When provided with context, use it to answer questions accurately. If no relevant context is provided, answer based on your general knowledge. Always be specific and helpful in your responses. Never just give generic greetings unless the user is actually greeting you."""
    
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
            
            logger.info(f"Sending to Groq API with model: {GROQ_MODEL}")
            logger.debug(f"User query: {user_query}")
            logger.debug(f"Context preview: {formatted_context[:200]}..." if len(formatted_context) > 200 else f"Context: {formatted_context}")
            
            # Get response from Groq
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            
            assistant_response = response.choices[0].message.content
            logger.info(f"Received response from Groq: {assistant_response[:100]}...")
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
                
                # Format context_used based on whether we have full results
                context_used = []
                if hasattr(self, '_last_results') and self._last_results:
                    # Use full results with score if available
                    context_used = [
                        {"text": result["text"], "score": result["score"]}
                        for result in self._last_results
                    ]
                elif context:
                    # Fallback to simple format if no results available
                    context_used = [{"text": text, "score": 1.0} for text in context]
                
                # Save assistant response
                token_count = response.usage.total_tokens if hasattr(response, 'usage') else None
                conversation_service.add_message(
                    conversation_id=self.conversation_id,
                    role="assistant",
                    content=assistant_response,
                    context_used=context_used,
                    model_used=GROQ_MODEL,
                    processing_time=processing_time,
                    token_count=token_count
                )
                
                # Store message info for return
                self._last_message_info = {
                    'context_used': context_used,
                    'token_count': token_count,
                    'processing_time': processing_time
                }
            
            logger.info(f"Generated response in {processing_time:.2f}s")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error in grqo_chat: {e}")
            return "Sorry, I encountered an error while processing your request."

    def process_and_store(self, file_path: str, conversation_id: Optional[int] = None):
        """Process document and store embeddings with conversation context"""
        try:
            file_ext = Path(file_path).suffix.lower()

            # Select appropriate loader based on file type
            if file_ext in ['.txt', '.md']:
                loader = TextLoader(file_path)
            elif file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_ext == '.docx':
                loader = Docx2txtLoader(file_path)
            elif file_ext == '.csv':
                loader = CSVLoader(file_path)
            elif file_ext == '.json':
                loader = JSONLoader(file_path, jq_schema='.', text_content=False)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

            documents = loader.load()

            # Extract text
            text = "\n".join([doc.page_content for doc in documents])

            # Chunk and embed
            chunks = self.embedder.chunk_text(text)
            embeddings = self.embedder.embed_chunks(chunks)

            # Store in Qdrant with conversation_id
            conv_id = conversation_id or self.conversation_id
            self.store.store(chunks, embeddings, conversation_id=conv_id)

            logger.info(f"Processed and stored {len(chunks)} chunks from {file_path} for conversation {conv_id}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    def query_with_context(self, query: str, top_k: int = 5) -> str:
        """Query with RAG context, isolated by conversation"""
        try:
            logger.info(f"Processing query: {query}")
            
            # Get query embedding
            query_embedding = self.embedder.embed_chunks([query])[0]

            # Search for similar chunks with conversation filter
            results = self.store.query(query_embedding, top_k=top_k, conversation_id=self.conversation_id)

            # Extract context text for the prompt
            context_text = [result["text"] for result in results]

            # Store results in instance for grqo_chat to use
            self._last_results = results

            # Generate response
            return self.grqo_chat(query, context_text)

        except Exception as e:
            logger.error(f"Error in query_with_context: {e}")
            # Return error response in same format
            return {
                "content": f"I encountered an error while processing your request: {str(e)}",
                "context_used": [],
                "token_count": 0,
                "processing_time": 0
            }