import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from trading_assistant.services.database.firestore_client import get_firestore_client
from trading_assistant.agent import root_agent

from dotenv import load_dotenv

from trading_assistant.observability import setup_observability

load_dotenv()
setup_observability(service_name="trading-bot-cli")


async def main():
    print("Starting Trading Bot...")
    user_id = select_user_id()
    session_service = InMemorySessionService()
    
    app_name = "trading_bot"
    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=session_service
    )
    
    session_id = f"{user_id}_session"
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state={"user_id": user_id}
    )
    
    print(f"Session created, ID: {session_id}")
    
    while True:
        user_input = input("\nEnter your trading query (or 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break
            
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )
        
        # print("\nProcessing your request...")
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            if hasattr(event, 'content') and event.content:
                parts = event.content.parts if hasattr(event.content, 'parts') else []
                if parts and hasattr(parts[0], 'text') and parts[0].text:
                    print(f"\n>>>{event.author}: {parts[0].text}")
                    # import pdb; pdb.set_trace()
                # else:
                #     print(f"\n{event.author}: [No text response]")
            
            # elif hasattr(event, 'get_function_calls'):
            #     if func_list := event.get_function_calls():
            #         print(f"[{event.author} calling functions: {len(func_list)}]")
            #         for i, func in enumerate(func_list):
            #             print(f"[Function call {i}] {func.name} args: {func.args}")
            
            elif hasattr(event, 'error_message') and event.error_message:
                print(f"[{event.author} error: {event.error_message}")

def select_user_id():
    print("\n=== User Selection ===")
    print("Available users:")
    
    try:
        db = get_firestore_client()
        portfolios = db.collection("portfolios").get()
        
        user_ids = []
        for doc in portfolios:
            user_id = doc.id
            user_ids.append(user_id)
            print(f"- {user_id}")
        
        if not user_ids:
            print("No users found in database. Using user1.")
            return "user1"
        
        chosen_id = input("\nEnter user ID (press Enter for user1): ")
        if not chosen_id:
            return "user1"
        
        if chosen_id in user_ids:
            print(f"Selected user: {chosen_id}")
            return chosen_id
        else:
            print(f"User {chosen_id} not found, using user1 instead.")
            return "user1"
            
    except Exception as e:
        print(f"Error accessing user database: {str(e)}")
        print("Using default user user1 instead.")
        return "user1"

if __name__ == "__main__":
    asyncio.run(main())
