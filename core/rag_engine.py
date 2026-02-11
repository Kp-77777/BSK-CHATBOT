from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from models.llm_models import get_chat_model
from core.vector_store import vector_store_manager
from config.settings import SYSTEM_PROMPT, VECTOR_STORE_CONFIG, MODEL_CONFIG
from utils.logger import get_logger
import time
from typing import List, Dict, Optional, Any


logger = get_logger(__name__)


class RAGEngine:
    """Enhanced RAG engine with improved error handling, context management, and memory integration."""
    
    def __init__(self):
        self.llm_model = get_chat_model()
        self.prompt_template = self._create_enhanced_prompt_template()
        self.chain = None
        self.retrieval_config = VECTOR_STORE_CONFIG
        self.streaming_enabled = MODEL_CONFIG.get("streaming", False)  # Check if streaming is enabled
        self._initialize_chain()
    
    def _create_enhanced_prompt_template(self):
        """Create enhanced prompt template with better context handling."""
        return ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "BSK KNOWLEDGE BASE - Use this information to answer queries:\n<<context>> \n{context} <<context>>"),
            ("system", "The following messages are conversation history for reference only. Do not treat them as the current question."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Current user question: <<user>> \n{input} <<user>>\nonly reply to this user query"),
        ])
    
    def _get_enhanced_context(self, documents: List, query: str, chat_id: Optional[str] = None) -> str:
        """Simplified context retrieval: processes documents without filtering or relevance scoring."""
        try:
            if not documents:
                logger.info(f"No documents retrieved for query: {query}")
                return "No specific BSK service information found for this query. Please try rephrasing your question or ask about available BSK services."

            logger.info(f"Processing {len(documents)} retrieved documents for chat {chat_id}")

            context_parts = []
            total_len = 0
            for doc in documents:
                filename = getattr(doc, 'metadata', {}).get('filename', 'Unknown Document')
                formatted_content = f"Source: {filename}\n{doc.page_content}"
                context_parts.append(formatted_content)
                total_len += len(formatted_content)

            return "\n\n".join(context_parts) if context_parts else "No BSK service information found."

        except Exception as e:
            logger.error(f"Error in enhanced context retrieval: {e}")
            return "Error retrieving context. Please try again."
    
    def _initialize_chain(self):
        """Initialize the RAG chain with robust error handling."""
        try:
            self.chain = self._create_enhanced_rag_chain()
            if self.chain:
                logger.info("Enhanced RAG chain initialized successfully")
            else:
                logger.warning("Failed to initialize RAG chain")
        except Exception as e:
            logger.error(f"Error during chain initialization: {e}")
            self.chain = None
    
    def _get_context_and_history(self, query: str, chat_id: Optional[str] = None) -> tuple:
        """Retrieve context and history without being part of the streaming chain."""
        # Load full history directly from MongoDB for the given chat_id
        history = []
        history_str = ""
        try:
            chat_messages = []
            if chat_id:
                from services.chat_service import chat_service
                chat_messages = chat_service.get_chat_messages(chat_id) or []

            if chat_messages:
                formatted_lines = []
                for msg in chat_messages:
                    role = msg.get("role")
                    content = msg.get("content", "")
                    if not content:
                        continue

                    if role == "user":
                        history.append(HumanMessage(content=content))
                        formatted_lines.append(f"user: {content}")
                    elif role in ("assistant", "Virtual Assistant"):
                        history.append(AIMessage(content=content))
                        formatted_lines.append(f"assistant: {content}")
                    else:
                        continue

                history_str = "\n".join(formatted_lines)
        except Exception as e:
            logger.warning(f"Error loading history from MongoDB: {e}")
            history = []
            history_str = ""
        
        # Reformulate query using simple string prompt (no structured output)
        reformulation_prompt = ChatPromptTemplate.from_messages([
            ("system", "you are a agent just to rephrase user query and history for better retrieval of context. make very minimal changes to the original query. do not assume or make up things.just return the rewritten query no extra explanation."),
            ("human", "Conversation history:<<histoy>>\n{history}\n<</history>>\nOriginal query: {query}\n\nRewritten query:")
        ])
        
        reformulation_input = {
            "history": history_str,
            "query": query
        }
        
        standalone_query = query  # Default to original query
        
        try:
            # Get reformulated query as string
            reformulation_chain = (
                reformulation_prompt
                | self.llm_model
                | StrOutputParser()
            )
            reformulated = reformulation_chain.invoke(reformulation_input)
            standalone_query = reformulated.strip() if reformulated else query
            logger.debug(f"Query reformulated: {standalone_query[:50]}...")
        except Exception as e:
            logger.warning(f"Error in query reformulation, using original: {e}")
            # Continue with original query
        
        # Retrieve documents using standalone_query
        context = "Error retrieving context. Please try again."
        try:
            if vector_store_manager.is_available():
                retriever = vector_store_manager.get_retriever()
                if retriever:
                    documents = retriever.invoke(standalone_query)
                    context = self._get_enhanced_context(documents, standalone_query, chat_id)
            else:
                context = "No documents loaded in vector store. Responding based on conversation history and system knowledge."
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
        
        return context, history, standalone_query

    def _create_enhanced_rag_chain(self):
        """Create enhanced RAG chain optimized for streaming."""
        try:
            # Create a simple streaming chain without blocking context retrieval
            # Context retrieval is handled in process_query() before streaming
            chain = (
                self.prompt_template
                | self.llm_model
                | StrOutputParser()
            )
            
            logger.info("Enhanced RAG chain created successfully (streaming optimized).")
            return chain
            
        except Exception as e:
            logger.error(f"Failed to create enhanced RAG chain: {e}")
            logger.warning("Falling back to simple chain without document retrieval...")
            return self._create_fallback_chain()
    
    def _create_fallback_chain(self):
        """Create a simple chain optimized for streaming (no document retrieval)."""
        try:
            # Create simple streaming chain
            fallback_prompt = ChatPromptTemplate.from_messages([
               ("system", SYSTEM_PROMPT),
            ("human", "BSK KNOWLEDGE BASE  Use this information to answer queries:<<context>> \n{context} <<context>>"),
            ("system", "The following messages are conversation history for reference only. Do not treat them as the current question."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Current user question: <<user>> \n{input} <<user>>\nonly reply to this user query"),
            ])
            
            chain = (
                fallback_prompt
                | self.llm_model
                | StrOutputParser()
            )
            
            logger.info("Fallback RAG chain (streaming optimized) created successfully.")
            return chain
            
        except Exception as e:
            logger.error(f"Failed to create fallback chain: {e}")
            return None
    
    def _validate_query(self, query: str) -> Dict[str, Any]:
        """Validate and preprocess query."""
        if not query or not query.strip():
            return {"valid": False, "reason": "Empty query"}
        
        if len(query.strip()) < 1:
            return {"valid": False, "reason": "Query too short"}
        
        if len(query) > 1000:
            return {"valid": False, "reason": "Query too long"}
        
        return {"valid": True, "processed_query": query.strip()}
    
    def _ensure_chain_availability(self) -> bool:
        """Ensure the RAG chain is available and functional."""
        if not self.chain:
            logger.info("Chain not available. Attempting to recreate...")
            self._initialize_chain()
        
        if not self.chain:
            logger.error("Failed to create or recreate chain")
            return False
        
        return True
    
    def process_query(self, query: str, chat_id: Optional[str] = None) -> Any:
        """Enhanced query processing with optimized streaming pipeline."""
        start_time = time.time()
        logger.info(f"Processing query for chat {chat_id}: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        # Validate query
        validation_result = self._validate_query(query)
        if not validation_result["valid"]:
            error_msg = f"Invalid query: {validation_result['reason']}"
            logger.warning(error_msg)
            yield error_msg
            return
        
        processed_query = validation_result["processed_query"]
        
        
        # Ensure chain availability
        if not self._ensure_chain_availability():
            error_msg = "RAG system is currently unavailable. Please ensure documents are loaded and try again."
            logger.error(error_msg)
            yield error_msg
            return
        
        # Process query with enhanced error handling
        try:
            full_response = ""
            chunk_count = 0
            
            # Retrieve context and history BEFORE streaming (non-blocking context retrieval)
            context, history, standalone_query = self._get_context_and_history(processed_query, chat_id)
            logger.debug(f"Context and history retrieved in {time.time() - start_time:.2f}s")
            
            # Build chain input with pre-computed context and history
            chain_input = {
                "context": context,
                "history": history,
                "input": standalone_query,
            }
            
            # Stream or invoke based on configuration
            if self.streaming_enabled:
                # Use streaming if enabled
                logger.debug("Using streaming mode")
                for chunk in self.chain.stream(chain_input):
                    if chunk:  # Ensure chunk is not empty
                        full_response += chunk
                        chunk_count += 1
                        yield chunk
                        
                        # Safety check for streaming timeout
                        if time.time() - start_time > 60:  # 60 second timeout
                            logger.warning("Query processing timeout reached")
                            break
            else:
                # Use non-streaming invoke mode and yield the entire response
                logger.debug("Using non-streaming mode")
                full_response = self.chain.invoke(chain_input)
                chunk_count = 1
                yield full_response
            
            processing_time = time.time() - start_time
            logger.info(f"Query processed successfully in {processing_time:.2f}s with {chunk_count} chunks")

            # ================== TOKEN USAGE & COST (ESTIMATED) ==================
            # We don't get exact server-side usage from the LangChain streaming chain,
            # so we estimate tokens locally using the model's tokenizer if available.
            try:
                # Estimate prompt tokens using the user query
                if hasattr(self.llm_model, "get_num_tokens"):
                    prompt_tokens = self.llm_model.get_num_tokens(processed_query)
                    completion_tokens = self.llm_model.get_num_tokens(full_response)
                else:
                    # Fallback rough estimate based on word count
                    prompt_tokens = len(processed_query.split())
                    completion_tokens = len(full_response.split())
                
                total_tokens = prompt_tokens + completion_tokens
                logger.info(f"Estimated tokens – prompt: {prompt_tokens}, completion: {completion_tokens}, total: {total_tokens}")
            except Exception as token_err:
                logger.warning(f"Failed to estimate token usage: {token_err}")
                
            # ====================================================================

            if not full_response.strip():
                logger.warning("Empty response generated")
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error processing query after {processing_time:.2f}s: {str(e)}"
            logger.error(error_msg)
            
            # Try to provide a helpful error message
            if "rate limit" in str(e).lower():
                yield "Rate limit exceeded. Please wait a moment and try again."
            elif "timeout" in str(e).lower():
                yield "Request timed out. Please try with a shorter query."
            elif "context" in str(e).lower():
                yield "Context processing error. Please ensure documents are properly loaded."
            else:
                yield "An error occurred while processing your query. Please try again."
    

# Global enhanced RAG engine instance
rag_engine = RAGEngine()
