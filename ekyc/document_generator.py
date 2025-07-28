"""
Document Generator untuk eKYC System
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from models import EKYCFormData, AnalysisResult
import logging

logger = logging.getLogger(__name__)

class EKYCDocumentGenerator:
    """Generator untuk dokumen eKYC"""
    
    def __init__(self, output_dir: str = "generated_documents"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_summary_report(self, form_data: EKYCFormData, analysis_results: Optional[Dict[str, AnalysisResult]] = None) -> str:
        """Generate ringkasan laporan eKYC"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ekyc_summary_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            # Prepare summary data
            summary = {
                "submission_info": {
                    "submission_id": form_data.submission_id,
                    "submission_date": form_data.submission_date.isoformat() if form_data.submission_date else None,
                    "status": form_data.status,
                    "generated_at": datetime.now().isoformat()
                },
                "personal_info": {
                    "full_name": form_data.personal_info.full_name,
                    "nik": form_data.personal_info.nik,
                    "birth_date": form_data.personal_info.birth_date,
                    "birth_place": form_data.personal_info.birth_place,
                    "gender": form_data.personal_info.gender,
                    "nationality": form_data.personal_info.nationality
                },
                "address": {
                    "full_address": form_data.address.full_address,
                    "city": form_data.address.city,
                    "province": form_data.address.province,
                    "postal_code": form_data.address.postal_code
                },
                "contact_info": {
                    "phone": form_data.contact_info.phone,
                    "email": form_data.contact_info.email
                },
                "documents": [
                    {
                        "document_type": doc.document_type,
                        "file_name": doc.file_name,
                        "file_size": doc.file_size,
                        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None
                    }
                    for doc in form_data.documents
                ],
                "analysis_results": {}
            }
            
            # Add analysis results if available
            if analysis_results:
                for doc_type, result in analysis_results.items():
                    summary["analysis_results"][doc_type] = {
                        "document_type": result.document_type,
                        "confidence_score": result.confidence_score,
                        "verification_status": result.verification_status,
                        "quality_score": getattr(result, 'quality_score', None),
                        "processing_time": getattr(result, 'processing_time', None)
                    }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Summary report generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise
    
    def generate_verification_certificate(self, form_data: EKYCFormData, verification_status: str = "VERIFIED") -> str:
        """Generate sertifikat verifikasi"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"verification_certificate_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            certificate = {
                "certificate_info": {
                    "certificate_id": f"CERT_{timestamp}",
                    "issued_date": datetime.now().isoformat(),
                    "issuer": "eKYC System",
                    "version": "1.0"
                },
                "subject_info": {
                    "full_name": form_data.personal_info.full_name,
                    "nik": form_data.personal_info.nik,
                    "verification_status": verification_status,
                    "submission_id": form_data.submission_id
                },
                "verification_details": {
                    "documents_verified": len(form_data.documents),
                    "verification_method": "Automated AI Analysis",
                    "compliance_status": "COMPLIANT",
                    "risk_level": "LOW"
                },
                "validity": {
                    "valid_from": datetime.now().isoformat(),
                    "valid_until": "2025-12-31T23:59:59",
                    "renewable": True
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(certificate, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Verification certificate generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating verification certificate: {e}")
            raise
    
    def generate_audit_log(self, form_data: EKYCFormData, actions: list) -> str:
        """Generate audit log"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_log_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            audit_log = {
                "audit_info": {
                    "log_id": f"AUDIT_{timestamp}",
                    "created_at": datetime.now().isoformat(),
                    "submission_id": form_data.submission_id,
                    "subject": form_data.personal_info.full_name
                },
                "actions": [
                    {
                        "timestamp": action.get("timestamp", datetime.now().isoformat()),
                        "action": action.get("action", "unknown"),
                        "details": action.get("details", ""),
                        "result": action.get("result", "success"),
                        "user_agent": action.get("user_agent", "system")
                    }
                    for action in actions
                ],
                "summary": {
                    "total_actions": len(actions),
                    "successful_actions": len([a for a in actions if a.get("result") == "success"]),
                    "failed_actions": len([a for a in actions if a.get("result") == "failed"]),
                    "duration": "N/A"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(audit_log, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Audit log generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating audit log: {e}")
            raise