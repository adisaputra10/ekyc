"""
Quick test script untuk knowledge base
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from add_knowledge import KnowledgeManager

async def test_knowledge_system():
    """Test basic functionality of knowledge system"""
    print("🧪 Testing Knowledge System...")
    
    try:
        # Initialize knowledge manager
        km = KnowledgeManager()
        print("✅ Knowledge manager initialized")
        
        # Test adding simple knowledge
        test_entry = km.create_knowledge_entry(
            title="Test Knowledge Entry",
            content="This is a test knowledge entry to verify the system works correctly.",
            category="test",
            tags=["test", "verification"]
        )
        
        success = await km.add_single_knowledge(test_entry)
        
        if success:
            print("✅ Test knowledge entry added successfully!")
            print("\n🎉 Knowledge system is working correctly!")
            print("\nNext steps:")
            print("1. Run 'python setup_knowledge_base.py' to add default knowledge")
            print("2. Run 'python add_knowledge.py' for interactive knowledge management")
            print("3. Test the RAG system via web interface")
        else:
            print("❌ Failed to add test knowledge entry")
            
    except Exception as e:
        print(f"❌ Error testing knowledge system: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_knowledge_system())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
