#!/usr/bin/env python3
"""
Simple test for OCR.space integration
Tests basic functionality without full imports
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_dependencies():
    """Test if required dependencies are installed"""
    print("🧪 Testing Dependencies...")
    
    # Test aiohttp
    try:
        import aiohttp
        print("✅ aiohttp is installed")
    except ImportError:
        print("❌ aiohttp not installed. Run: pip install aiohttp==3.9.3")
        return False
    
    # Test PDF libraries
    pdf_libs = []
    
    try:
        import pypdfium2
        pdf_libs.append("pypdfium2")
        print("✅ pypdfium2 is installed")
    except ImportError:
        print("⚠️  pypdfium2 not installed (optional)")
    
    try:
        import fitz
        pdf_libs.append("PyMuPDF")
        print("✅ PyMuPDF is installed")
    except ImportError:
        print("⚠️  PyMuPDF not installed (optional)")
    
    if not pdf_libs:
        print("⚠️  No PDF libraries found. Some features may be limited.")
        print("   Install with: pip install pypdfium2")
    
    # Test OCR.space API key
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if api_key:
        print(f"✅ OCR_SPACE_API_KEY found: {api_key[:10]}...")
    else:
        print("❌ OCR_SPACE_API_KEY not set")
        print("   Set with: export OCR_SPACE_API_KEY='your-api-key'")
        print("   Get free key from: https://ocr.space/ocrapi")
        return False
    
    return True

def test_ocr_service_import():
    """Test if OCR service can be imported"""
    print("\n🧪 Testing OCR Service Import...")
    
    try:
        from app.services.ocr_service import OCRSpaceService
        print("✅ OCRSpaceService imports successfully")
        
        # Create instance
        ocr_service = OCRSpaceService()
        print("✅ OCRSpaceService instance created")
        
        return True
    except Exception as e:
        print(f"❌ Error importing OCRSpaceService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_availability():
    """Check if test PDFs are available"""
    print("\n🧪 Checking for Test PDFs...")
    
    uploads_dir = Path("storage/uploads")
    if not uploads_dir.exists():
        print(f"❌ Uploads directory not found: {uploads_dir}")
        return False
    
    pdf_files = list(uploads_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in storage/uploads/")
        print("   Upload a PDF via the web interface first")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF file(s):")
    for pdf in pdf_files[:3]:  # Show first 3
        size = pdf.stat().st_size
        print(f"   - {pdf.name} ({size:,} bytes)")
    
    if len(pdf_files) > 3:
        print(f"   ... and {len(pdf_files) - 3} more")
    
    return True

def main():
    """Main test function"""
    print("="*50)
    print("OCR.space Integration - Quick Test")
    print("="*50)
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_dependencies():
        tests_passed += 1
    
    if test_ocr_service_import():
        tests_passed += 1
    
    if test_pdf_availability():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n🎉 All tests passed! OCR.space integration is ready.")
        print("\nNext steps:")
        print("1. Run the full test: python test_ocr_integration.py")
        print("2. Start server: uvicorn app.main:app --reload")
        print("3. Test with web interface at http://localhost:5173")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        
        if tests_passed >= 2:
            print("\nYou can still try the integration:")
            print("1. Set OCR_SPACE_API_KEY environment variable")
            print("2. Run: python test_ocr_integration.py")
            print("   (It will ask for confirmation before using API credits)")

if __name__ == "__main__":
    main()