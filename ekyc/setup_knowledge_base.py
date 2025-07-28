"""
Batch script untuk menambahkan knowledge default ke RAG system
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from models import KnowledgeBaseEntry
from ai_document_analyzer import VectorDatabase, DocumentProcessor
from config import Settings
from add_knowledge import KnowledgeManager, EKYC_KNOWLEDGE_BASE

async def add_default_knowledge():
    """Add all default eKYC knowledge to RAG system"""
    print("🚀 Adding default eKYC knowledge to RAG system...")
    print("=" * 60)
    
    try:
        # Initialize knowledge manager
        km = KnowledgeManager()
        
        # Add all default knowledge
        print(f"📚 Adding {len(EKYC_KNOWLEDGE_BASE)} knowledge entries...")
        results = await km.add_knowledge_from_dict(EKYC_KNOWLEDGE_BASE)
        
        # Display results
        print("\n📊 Results:")
        success_count = 0
        for title, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {title}")
            if success:
                success_count += 1
        
        print(f"\n📈 Summary:")
        print(f"Total entries: {len(results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(results) - success_count}")
        print(f"Success rate: {(success_count/len(results)*100):.1f}%")
        
        if success_count > 0:
            print(f"\n🎉 Successfully added {success_count} knowledge entries to RAG system!")
            print("\nSistem sekarang dapat menjawab pertanyaan tentang:")
            categories = set()
            for entry in EKYC_KNOWLEDGE_BASE:
                categories.add(entry['category'])
            
            for category in sorted(categories):
                entries_in_category = [e for e in EKYC_KNOWLEDGE_BASE if e['category'] == category]
                print(f"\n📁 {category.title()}:")
                for entry in entries_in_category:
                    if results.get(entry['title'], False):
                        print(f"  ✅ {entry['title']}")
        
        print(f"\n🔍 Test the RAG system by asking questions like:")
        print(f"  - 'Apa saja persyaratan untuk membuat KTP?'")
        print(f"  - 'Bagaimana cara validasi NIK?'")
        print(f"  - 'Dokumen apa saja yang diterima sistem eKYC?'")
        print(f"  - 'Bagaimana proses verifikasi eKYC?'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(add_default_knowledge())
    sys.exit(0 if success else 1)
