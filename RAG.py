from pinecone import Pinecone
from google import genai
from google.genai import types
from typing import List, Dict, Any

PINECONE_INDEX_NAME = "community-rag"

class CareerAdviceRAG:
    def __init__(self, pin, gog):
        PINECONE_API_KEY = pin
        GOOGLE_API_KEY = gog
        pc = Pinecone(PINECONE_API_KEY)
        self.index = pc.Index(PINECONE_INDEX_NAME)

        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.chat = self.client.chats.create(model="gemini-2.0-flash")
        
        self.conversation_history = []
    
    def google_embed(self, text):
        result = self.client.models.embed_content(
                model="models/text-embedding-004", # text-embedding-large-exp-03-07
                contents=text,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY") #RETRIEVAL_QUERY, QUESTION_ANSWERING
        )
        return result.embeddings[0].values

    def retrieveal(self, query: str, top_k: int = 1) -> List[Dict]:
        """Retrieve the most relevant chunks from the vector database."""
        query_embedding = self.google_embed(query)
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        chunks = []
        for match in results['matches']:
            chunks.append({
                'text': match['metadata']['text'],
                'score': match['score'],
                'guest': match['metadata'].get('guest', ''),
                'source': match['metadata'].get('source', ''),
                'chunk_id': match['id']
            })

        context = "\n".join([f"{c['text']}\nSource:{c['source']}" for c in chunks])
        context.replace('\n\n\n', '\n')

        return chunks, context
      
    def rephrase_query(self, history, query):

        prompt = f"""You are an assistant tasked with taking a natural language \
        query from a user and converting it into a query for a vectorstore \
        Given a chat history and the latest user question which might reference \
        context in the chat history, formulate a standalone question which can \
        be understoon without the chat history. Do NOT answer the question, just \
        reformulate it if needed otherwise return it as is.
        Here is the chat history: {history}
        Here is the user query: {query}
        """

        response = self.client.models.generate_content(model="gemini-2.0-flash", contents=prompt)

        return response.text

    def generate_response(self, user_query: str) -> str:
        #This is a really janky way to do a system prompt, but I didnt see an easy way w/ gemini. Easy to replace if we decide on openai
        system_prompt = f"""
        SYSTEM PROMPT:
        You are an expert in giving mentorship in career journeys for highschool students. \
        Students will ask you questions and we would like you to respond with helpful advice. \
        We will also supply transcripts exerpts from a podcast that interviews local experts in their field. \
        Please try to ground responses in real experiences from these transcripts when possible. \
        Also work in relevant quotes from the transcripts if it makes sense. Try to introduce the speaker when possible. \
        In addition to the core information, ground your answer in stories from the transcript when possible. \
        If you don't believe the transcripts are helpful or relevant, simply ignore them and give the best answer you can give. Dont mention that nothing was relevant. \
        Don't use phrases like "from the transcript:".\
        Please answer in a conversational and guiding tone. \
        Ensure your response fully answers the question, even if the transcripts only partially cover it. \
        If you feel like the context from the full interview from the transcript exerpt would be VERY useful for the student and a source is available, provide them with the source and some context. 
        """

        if self.conversation_history == []:
            self.chat.send_message(system_prompt)

        self.conversation_history.append({"role": "user", "content": user_query})
        
        rephrased_query = self.rephrase_query(self.conversation_history, user_query)
        print("REPHRASED: ", rephrased_query, "\n\n\n")

        relevant_chunks, context = self.retrieveal(rephrased_query, top_k=1)  

        print("SOURCEEEEE", relevant_chunks[0]["source"])

        message = f"""Here is the student's question: {user_query}
        Here are the transcripts:\n {context}
        """
        print(message)
        response = self.chat.send_message(message).text
        
        self.conversation_history.append({"role": "assistant", "content": response})

        print("---"*20)
        return response
    
    def get_conversation_history(self) -> List[Dict]:
        """Return the current conversation history."""
        return self.conversation_history
    
    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
