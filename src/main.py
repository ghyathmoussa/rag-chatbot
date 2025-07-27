#!/usr/bin/env python3
from src.models.groq_model import GroqModel
from src.database.conversation_service import conversation_service
from src.database.connection import db_manager
from src.utils.logger import logger
import sys


def main():
    """Main entry point for the RAG chatbot"""
    logger.info("Starting RAG Chatbot...")
    
    # Test database connection
    if not db_manager.test_connection():
        logger.error("Failed to connect to database. Exiting.")
        sys.exit(1)
    
    # Create a new conversation
    conversation = conversation_service.create_conversation(
        user_id="demo_user",
        title="RAG Chatbot Demo"
    )
    
    # Initialize GroqModel with conversation
    groq_model = GroqModel(conversation_id=conversation['id'])
    
    logger.info(f"Created conversation: {conversation['session_id']}")
    print(f"\nRAG Chatbot started. Conversation ID: {conversation['session_id']}")
    print("Type 'quit' to exit, 'load <filepath>' to load a document\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                print("Goodbye!")
                break
            
            if user_input.lower().startswith('load '):
                # Load document
                file_path = user_input[5:].strip()
                try:
                    groq_model.process_and_store(file_path)
                    print(f"✓ Document loaded: {file_path}")
                except Exception as e:
                    print(f"✗ Error loading document: {e}")
                continue
            
            # Query with context
            response = groq_model.query_with_context(user_input)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()