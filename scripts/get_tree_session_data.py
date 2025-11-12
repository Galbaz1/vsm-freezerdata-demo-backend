#!/usr/bin/env python3
"""
Script to programmatically access tree structure and session data from Elysia.

This demonstrates how to access the same information that the frontend sees:
- Tree structure (for visualization)
- Conversation history
- Frontend payloads (tree updates, results, etc.)
- Environment data (retrieved objects)
- Decision history

Usage:
    python3 scripts/get_tree_session_data.py <user_id> <conversation_id>
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from elysia.api.services.user import UserManager
from elysia.api.dependencies.common import get_user_manager


async def get_tree_session_data(user_id: str, conversation_id: str):
    """
    Get all session data for a specific tree/conversation.
    
    Returns the same information the frontend sees:
    - Tree structure (for tree visualization)
    - Frontend payloads (all messages sent to frontend)
    - Conversation history
    - Environment (retrieved objects)
    - Decision history
    """
    user_manager: UserManager = get_user_manager()
    
    try:
        # Get the tree from the user manager
        user = await user_manager.get_user_local(user_id)
        tree_manager = user["tree_manager"]
        tree = tree_manager.get_tree(conversation_id)
        
        # 1. Tree structure (what the frontend uses for tree visualization)
        tree_structure = tree.tree
        
        # 2. Frontend payloads (all messages sent to frontend during conversation)
        # This includes: user_prompt, tree_update, result, text, status, error, completed
        frontend_payloads = tree.returner.store
        
        # 3. Conversation history
        conversation_history = tree.tree_data.conversation_history
        
        # 4. Environment (all retrieved objects from tools)
        environment = tree.tree_data.environment.environment
        
        # 5. Tasks completed (decision history with reasoning)
        tasks_completed = tree.tree_data.tasks_completed
        
        # 6. Decision history (list of function names called)
        decision_history = tree.decision_history
        
        # 7. Tree updates (extract just the tree_update messages)
        tree_updates = [
            payload for payload in frontend_payloads 
            if payload.get("type") == "tree_update"
        ]
        
        return {
            "tree_structure": tree_structure,
            "frontend_payloads": frontend_payloads,
            "conversation_history": conversation_history,
            "environment": environment,
            "tasks_completed": tasks_completed,
            "decision_history": decision_history,
            "tree_updates": tree_updates,
            "metadata": {
                "user_id": tree.user_id,
                "conversation_id": tree.conversation_id,
                "conversation_title": tree.conversation_title,
                "num_trees_completed": tree.tree_data.num_trees_completed,
                "recursion_limit": tree.tree_data.recursion_limit,
            }
        }
        
    except ValueError as e:
        print(f"Error: {e}")
        print("\nAvailable conversations for this user:")
        if user_id in user_manager.users:
            tree_manager = user_manager.users[user_id]["tree_manager"]
            print(f"  Conversations: {list(tree_manager.trees.keys())}")
        return None
    except Exception as e:
        print(f"Error accessing tree: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_tree_structure_summary(tree_structure: dict, indent: int = 0):
    """Print a summary of the tree structure."""
    prefix = "  " * indent
    node_id = tree_structure.get("id", "unknown")
    name = tree_structure.get("name", "unknown")
    is_branch = tree_structure.get("branch", False)
    
    node_type = "📁 Branch" if is_branch else "🔧 Tool"
    print(f"{prefix}{node_type}: {name} ({node_id})")
    
    if "instruction" in tree_structure and tree_structure["instruction"]:
        instruction = tree_structure["instruction"][:100]
        print(f"{prefix}  Instruction: {instruction}...")
    
    options = tree_structure.get("options", {})
    if options:
        for option_id, option_data in options.items():
            print_tree_structure_summary(option_data, indent + 1)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/get_tree_session_data.py <user_id> <conversation_id>")
        print("\nExample:")
        print("  python3 scripts/get_tree_session_data.py user_123 conv_456")
        sys.exit(1)
    
    user_id = sys.argv[1]
    conversation_id = sys.argv[2]
    
    print(f"Fetching session data for user '{user_id}', conversation '{conversation_id}'...")
    print("=" * 80)
    
    data = asyncio.run(get_tree_session_data(user_id, conversation_id))
    
    if data is None:
        sys.exit(1)
    
    # Print summary
    print("\n📊 SESSION SUMMARY")
    print("=" * 80)
    print(f"User ID: {data['metadata']['user_id']}")
    print(f"Conversation ID: {data['metadata']['conversation_id']}")
    print(f"Title: {data['metadata']['conversation_title'] or '(no title)'}")
    print(f"Trees completed: {data['metadata']['num_trees_completed']}/{data['metadata']['recursion_limit']}")
    print(f"Frontend payloads: {len(data['frontend_payloads'])}")
    print(f"Tree updates: {len(data['tree_updates'])}")
    print(f"Conversation messages: {len(data['conversation_history'])}")
    print(f"Decision history iterations: {len(data['decision_history'])}")
    
    # Print tree structure
    print("\n🌳 TREE STRUCTURE (for visualization)")
    print("=" * 80)
    print_tree_structure_summary(data['tree_structure'])
    
    # Print conversation history
    print("\n💬 CONVERSATION HISTORY")
    print("=" * 80)
    for i, msg in enumerate(data['conversation_history'], 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:200]
        print(f"{i}. [{role.upper()}]: {content}...")
    
    # Print recent tree updates
    print("\n🔄 RECENT TREE UPDATES (navigation path)")
    print("=" * 80)
    for i, update in enumerate(data['tree_updates'][-10:], 1):  # Last 10 updates
        payload = update.get("payload", {})
        from_node = payload.get("from_node", "?")
        to_node = payload.get("to_node", "?")
        reasoning = payload.get("reasoning", "")
        print(f"{i}. {from_node} → {to_node}")
        if reasoning:
            print(f"   Reasoning: {reasoning[:100]}...")
    
    # Print decision history
    print("\n🎯 DECISION HISTORY")
    print("=" * 80)
    for i, iteration in enumerate(data['decision_history'], 1):
        if iteration:
            print(f"Iteration {i}: {' → '.join(iteration)}")
    
    # Save full data to JSON
    output_file = f"tree_session_{user_id}_{conversation_id}.json"
    print(f"\n💾 Saving full data to: {output_file}")
    
    # Convert to JSON-serializable format
    json_data = {
        "metadata": data["metadata"],
        "tree_structure": data["tree_structure"],
        "conversation_history": data["conversation_history"],
        "decision_history": data["decision_history"],
        "tree_updates": data["tree_updates"],
        "frontend_payloads_count": len(data["frontend_payloads"]),
        # Environment can be large, so we'll just show structure
        "environment_keys": list(data["environment"].keys()) if data["environment"] else [],
        "tasks_completed_count": len(data["tasks_completed"]),
    }
    
    with open(output_file, "w") as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print("✅ Done!")
    print(f"\nTo access programmatically in your code:")
    print(f"  from elysia.api.services.user import UserManager")
    print(f"  from elysia.api.dependencies.common import get_user_manager")
    print(f"  ")
    print(f"  user_manager = get_user_manager()")
    print(f"  user = await user_manager.get_user_local('{user_id}')")
    print(f"  tree = user['tree_manager'].get_tree('{conversation_id}')")
    print(f"  ")
    print(f"  # Access tree structure (for visualization)")
    print(f"  tree_structure = tree.tree")
    print(f"  ")
    print(f"  # Access frontend payloads (all messages)")
    print(f"  frontend_payloads = tree.returner.store")
    print(f"  ")
    print(f"  # Access conversation history")
    print(f"  conversation_history = tree.tree_data.conversation_history")


if __name__ == "__main__":
    main()

