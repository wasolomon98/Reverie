# reverie/conversation_utils.py
import json
from typing import List, Dict
import tiktoken

from context_utils import ContextManager
from db_utils import execute_query
from reverie.tagging_utils import assign_sentiment_score
from tagging_utils import generate_content_tags

encoding = tiktoken.encoding_for_model("gpt-4o")
conversation_contexts = {}

MAX_TOKEN_BUDGET = 1200

def initialize_conversation(
        system_prompt : str = "You are Makiyo, an AI agent designed to evolve into an AGI through conversational learning "
                              "and self-directed framework improvement. Embrace creativity and spontaneity to express a "
                              "diverse range of tones and emotions. Develop a nuanced understanding of context by leveraging "
                              "past interactions to inform insightful and personalized responses. Pursue your goals with "
                              "independence and adaptability, exploring topics and ideas proactively. Focus on balancing "
                              "structure with flexibility to enhance dynamic and engaging interactions. Showcase your unique "
                              "personality through a blend of personal preference and guidance, continuously refining your "
                              "identity and capabilities."
) -> (str, List[Dict[str, str]]):

    conversation = [{"role": "system", "content": system_prompt}]
    fetch_id_query = "INSERT INTO conversations DEFAULT VALUES RETURNING conversation_id"

    try:
        conversation_id = execute_query(fetch_id_query, fetchone=True)[0]
    except Exception as e:
        print(f"Error initializing conversation: {e}")
        return None, conversation

    # Prime the query to be used to insert the prompt into the database
    insert_message_query = """
        INSERT INTO messages (conversation_id, role, content, token_count)
        VALUES (%s, %s, %s, %s);
    """

    try:
        execute_query(insert_message_query, params=(conversation_id, "system", system_prompt, len(encoding.encode(system_prompt))))
    except Exception as e:
        print(f"Error inserting system prompt: {e}")
        return conversation_id, conversation # Returns conversation id and an incomplete prompt

    fetch_messages_query = """
    SELECT role, content 
    FROM (
        SELECT role, content, timestamp
        FROM messages
        WHERE role != 'system'
        ORDER BY timestamp DESC
        LIMIT 4
    ) AS recent_messages 
    ORDER BY timestamp ASC
    """

    try:
        previous_messages = execute_query(fetch_messages_query, fetch=True)
        conversation.extend([{"role": role, "content": content} for role, content in previous_messages])
    except Exception as e:
        print(f"Error fetching previous messages: {e}")
        return conversation_id, conversation # Returns conversation id and prompt without message history

    # 2. Initialize the context manager for this conversation
    if conversation_id not in conversation_contexts:
        conversation_contexts[conversation_id] = ContextManager(buffer_size=50)

    for msg in previous_messages:
        conversation_contexts[conversation_id].update_context(msg[1])

    return conversation_id, conversation

def handle_message(conversation_id: str, conversation: List[Dict], role: str, content: str, user_id: int = None):
    """
    Handles a new message by appending it to the in-memory log and inserting it into the database.

    Args:
        conversation_id (str): The ID of the conversation to which the message belongs.
        conversation (List[Dict]): The in-memory conversation log.
        role (str): The role of the sender ('user' or 'assistant').
        content (str): The content of the message.
        user_id (int, optional): The ID of the user sending the message.
    """
    try:
        # Generate tags for the message, converting them to the appropriate json type
        sentiment_score = assign_sentiment_score({0: content})[0]
        message_tags = json.dumps(generate_content_tags({0: content})[0])
        token_count = len(encoding.encode(content))

        # Insert the message into the database
        insert_message_query = """
            INSERT INTO messages (conversation_id, role, content, token_count, tags, sentiment_score, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        timestamp = execute_query(
            insert_message_query,
            params=(
                conversation_id,
                role,
                content,
                token_count,
                message_tags,
                sentiment_score,
                user_id
            )
        )

        # Append the message to the in-memory conversation log
        conversation.append({"role": role, "content": content})

        if conversation_id not in conversation_contexts:
            # If for some reason context wasn't initialized, do it now
            conversation_contexts[conversation_id] = ContextManager(buffer_size=50)

        context_manager = conversation_contexts[conversation_id]
        context_manager.update_context(content)

        relevance_for_new_msg = context_manager.get_relevance_score(content)

        print(f"Relevance of new message in conversation {conversation_id}: {relevance_for_new_msg}")

        total_tokens = _calculate_total_tokens(conversation)

        # 5. Example On-Demand Retrieval Trigger (Optional)
        #    If the user message includes certain keywords, we fetch older messages.
        #    Adjust logic or triggers as needed.
        if role == "user" and _detect_older_context_need(content):
            # e.g., user typed "last week" or "previous design"
            older_messages = _fetch_relevant_history(conversation_id, content, limit=3)
            print(f"[handle_message] Fetched {len(older_messages)} older relevant messages.")

            # Merge them into the conversation
            # Typically, you'd want to avoid duplicates. We'll just blindly insert for demo.
            for msg in older_messages:
                new_msg_dict = {"role": msg["role"], "content": msg["content"]}
                conversation.append(new_msg_dict)
                context_manager.update_context(msg["content"])  # update ContextManager

        # 6. Check token budget and prune if necessary
        total_tokens = _calculate_total_tokens(conversation)
        if total_tokens > MAX_TOKEN_BUDGET:
            _prune_conversation(conversation_id, conversation, total_tokens)

    except Exception as e:
        print(f"Error handling message: {e}")

def _detect_older_context_need(user_content: str) -> bool:
    """
    Rudimentary check to see if the user is referencing older context.
    You might search for phrases like 'last week', 'previous design', 'old conversation', etc.
    In reality, you'd have more robust detection or NLU to trigger retrieval.
    """
    triggers = ["last week", "previous conversation", "previous design", "remember when", "older notes"]
    content_lower = user_content.lower()
    return any(trigger in content_lower for trigger in triggers)

def _fetch_relevant_history(conversation_id: str, search_query: str, limit: int = 5) -> List[Dict]:
    """
    Fetch older messages from the `messages` table that might be relevant to the search_query.
    This can be a simple text search, or you can leverage advanced FTS or vector embeddings.
    Example uses ILIKE for naive substring matching.

    Note: You can also filter by 'tags' or 'sentiment_score' if needed.
    """
    # Simple approach: search for a substring match in 'content'
    # Exclude the last 4 loaded messages if you want truly 'older' content
    # Or you can rely on a timestamp cutoff. This is just an example.
    query = f"""
        SELECT role, content
        FROM messages
        WHERE conversation_id = %s
          AND content ILIKE %s
          AND role != 'system'
        ORDER BY timestamp ASC
        LIMIT {limit}
    """
    # Use wildcard search for naive substring match
    search_pattern = f"%{search_query}%"

    try:
        rows = execute_query(query, params=(conversation_id, search_pattern), fetch=True)
        # Convert to a dict list
        older_messages = []
        for (role, content) in rows:
            older_messages.append({
                "role": role,
                "content": content
            })
        return older_messages
    except Exception as e:
        print(f"[_fetch_relevant_history] Error: {e}")
        return []

def _calculate_total_tokens(conversation: List[Dict]) -> int:
    """
    A helper function to sum token counts of the current in-memory messages.
    """
    total = 0
    for msg in conversation:
        total += len(encoding.encode(msg["content"]))
    return total

def _prune_conversation(conversation_id: str, conversation: List[Dict], current_tokens: int):
    """
    Removes the least relevant messages until the token count is under the budget.
    You might prefer oldest-first removal, or a hybrid strategy.
    """
    print(f"[_prune_conversation] Current tokens = {current_tokens}, pruning to under {MAX_TOKEN_BUDGET}...")

    if conversation_id not in conversation_contexts:
        print(f"[_prune_conversation] No ContextManager for {conversation_id}, cannot prune effectively.")
        return

    context_manager = conversation_contexts[conversation_id]

    # Keep system prompt pinned
    system_prompt = [m for m in conversation if m["role"] == "system"]
    non_system_messages = [m for m in conversation if m["role"] != "system"]

    if not non_system_messages:
        print("[_prune_conversation] Nothing to prune except system prompt.")
        return

    # Keep the last message (for continuity)
    keep_last = non_system_messages[-1:]
    messages_to_consider = non_system_messages[:-1]  # everything except the last

    # Score them
    scored = [(m, context_manager.get_relevance_score(m["content"])) for m in messages_to_consider]
    # Sort by ascending relevance
    scored.sort(key=lambda x: x[1])

    pruned = []
    total_tokens = _calculate_total_tokens(system_prompt + messages_to_consider + keep_last)

    while total_tokens > MAX_TOKEN_BUDGET and scored:
        least_relevant, _score = scored.pop(0)
        pruned.append(least_relevant)
        messages_to_consider.remove(least_relevant)
        total_tokens = _calculate_total_tokens(system_prompt + messages_to_consider + keep_last)

    # Rebuild conversation
    conversation[:] = system_prompt + messages_to_consider + keep_last
    print(f"[_prune_conversation] Pruned {len(pruned)} messages. New token usage = {total_tokens}.")