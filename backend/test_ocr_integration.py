#!/usr/bin/env python3
"""
Test script for OCR.space integration
Run with: python test_ocr_integration.py
Make sure to set OCR_SPACE_API_KEY environment variable first
"""
import os
import asyncio
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ocr_service import OCRSpaceService


async def test_ocr_service():
    """Test the OCR.space integration"""
    
    # Check for API key
    api_key = os.getenv("OCR_SPACE_API_KEY")
    if not api_key:
        print("❌ ERROR: OCR_SPACE_API_KEY environment variable not set")
        print("Set it with: export OCR_SPACE_API_KEY='your-api-key'")
        return False
    
    print(f"✅ OCR_SPACE_API_KEY found: {api_key[:10]}...")
    
    # Create OCR service
    ocr_service = OCRSpaceService(api_key=api_key)
    
    # Find a test PDF
    test_pdfs = list(Path("storage/uploads").glob("*.pdf"))
    if not test_pdfs:
        print("❌ No test PDFs found in storage/uploads/")
        print("Please upload a PDF first via the web interface")
        return False
    
    test_pdf = test_pdfs[0]
    print(f"✅ Found test PDF: {test_pdf.name} ({test_pdf.stat().st_size:,} bytes)")
    
    # Test PDF splitting logic
    file_size = test_pdf.stat().st_size
    if file_size > ocr_service.max_file_size:
        print(f"⚠️  PDF is large ({file_size:,} bytes > 1MB), will be split into chunks")
    
    # Estimate cost
    num_requests, estimated_cost = ocr_service.estimate_ocr_cost(test_pdf)
    print(f"📊 Estimated: {num_requests} API requests, cost: ${estimated_cost:.4f}")
    
    # Ask for confirmation
    print("\n⚠️  This will use your OCR.space API credits")
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Test cancelled")
        return False
    
    # Run OCR
    print(f"\n🚀 Starting OCR extraction...")
    try:
        extracted_text = await ocr_service.extract_text_from_pdf(test_pdf, language="eng")
        
        if extracted_text:
            print(f"✅ Success! Extracted {len(extracted_text):,} characters")
            print("\n📄 Sample of extracted text (first 500 chars):")
            print("-" * 50)
            print(extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text)
            print("-" * 50)
            
            # Save to file for inspection
            output_file = Path("test_ocr_output.txt")
            output_file.write_text(extracted_text)
            print(f"\n💾 Full output saved to: {output_file}")
            
            return True
        else:
            print("❌ No text extracted")
            return False
            
    except Exception as e:
        print(f"❌ Error during OCR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_converter_integration():
    """Test the converter with OCR integration"""
    print("\n" + "="*50)
    print("Testing Converter Integration")
    print("="*50)
    
    try:
        from app.services.converter import PDFConverter
    except ImportError as e:
        print(f"❌ Could not import PDFConverter: {e}")
        print("This is likely due to PyMuPDF library issues.")
        print("The OCR service still works independently.")
        return False
    
    # Find a test PDF
    test_pdfs = list(Path("storage/uploads").glob("*.pdf"))
    if not test_pdfs:
        print("❌ No test PDFs found")
        return False
    
    test_pdf = test_pdfs[0]
    
    # Create converter
    converter = PDFConverter()
    
    print(f"Testing converter with: {test_pdf.name}")
    print("This will test the full pipeline with OCR.space integration")
    
    # Ask for confirmation
    response = input("Run full conversion test? (y/N): ").strip().lower()
    if response != 'y':
        print("Test cancelled")
        return False
    
    try:
        # Run conversion (without actually creating EPUB to save time)
        print("\n🚀 Testing text extraction only...")
        text_layer = await converter._extract_text_layer(test_pdf)
        
        print(f"✅ Text extraction successful!")
        print(f"📄 Extracted {len(text_layer):,} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in converter: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🧪 OCR.space Integration Test")
    print("="*50)
    
    # Test 1: OCR Service
    print("\n1. Testing OCR Service...")
    ocr_success = await test_ocr_service()
    
    # Test 2: Converter Integration
    print("\n2. Testing Converter Integration...")
    converter_success = await test_converter_integration()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    if ocr_success:
        print("✅ OCR Service: PASS")
    else:
        print("❌ OCR Service: FAIL")
    
    if converter_success:
        print("✅ Converter Integration: PASS")
    else:
        print("❌ Converter Integration: FAIL")
    
    if ocr_success and converter_success:
        print("\n🎉 All tests passed! OCR.space integration is ready.")
        print("\nNext steps:")
        print("1. Set OCR_SPACE_API_KEY in your production environment")
        print("2. Deploy the updated backend")
        print("3. Test with actual PDF conversions")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())