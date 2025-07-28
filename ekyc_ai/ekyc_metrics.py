#!/usr/bin/env python3
"""
eKYC Metrics and Comparison Module
Membandingkan performa eKYC AI vs Manual Process
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import statistics
from enum import Enum

class ProcessType(Enum):
    AI_AUTOMATED = "AI_Automated"
    MANUAL = "Manual"
    HYBRID = "Hybrid"

class ValidationStatus(Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    PARTIAL = "PARTIAL"
    NEEDS_REVIEW = "NEEDS_REVIEW"

@dataclass
class ValidationMetrics:
    """Metrics untuk satu proses validasi"""
    document_type: str  # KTP, AKTA, etc
    process_type: ProcessType
    start_time: datetime
    end_time: datetime
    processing_time_seconds: float
    validation_status: ValidationStatus
    confidence_score: float
    fields_extracted: int
    fields_missing: int
    accuracy_score: float  # Manual verification accuracy
    cost_estimate: float  # Estimated cost in IDR
    human_review_required: bool
    errors_found: List[str]
    warnings_found: List[str]

class eKYCMetricsCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics_data: List[ValidationMetrics] = []
        self.manual_baseline = self._load_manual_baseline()
    
    def _load_manual_baseline(self) -> Dict:
        """Load baseline metrics dari proses manual eKYC"""
        return {
            "average_processing_time_minutes": {
                "ktp": 8.5,  # 8.5 menit rata-rata manual verification KTP
                "akta": 25.0,  # 25 menit rata-rata manual verification Akta
                "comprehensive": 35.0  # Full document verification
            },
            "accuracy_rate": {
                "ktp": 0.94,  # 94% accuracy manual verification
                "akta": 0.89,  # 89% accuracy manual verification
                "comprehensive": 0.91
            },
            "cost_per_verification_idr": {
                "ktp": 15000,  # IDR 15,000 per KTP verification
                "akta": 75000,  # IDR 75,000 per Akta verification
                "comprehensive": 95000  # IDR 95,000 comprehensive
            },
            "human_hours_required": {
                "ktp": 0.14,  # 8.5 minutes = 0.14 hours
                "akta": 0.42,  # 25 minutes = 0.42 hours
                "comprehensive": 0.58
            },
            "error_rate": {
                "ktp": 0.06,  # 6% error rate
                "akta": 0.11,  # 11% error rate
                "comprehensive": 0.09
            }
        }
    
    def start_validation(self, document_type: str, process_type: ProcessType) -> str:
        """Mulai tracking validasi"""
        validation_id = f"{document_type}_{process_type.value}_{int(time.time())}"
        return validation_id
    
    def record_validation(self, 
                         document_type: str, 
                         process_type: ProcessType,
                         processing_time: float,
                         validation_result: Dict,
                         manual_verification_result: Dict = None) -> ValidationMetrics:
        """Record metrics dari hasil validasi"""
        
        # Extract data dari validation result
        status = ValidationStatus(validation_result.get('status', 'INVALID'))
        confidence = validation_result.get('confidence', 0) / 100.0
        
        # Count fields
        extracted_fields = validation_result.get('validation_details', {}).get('extracted_fields', {})
        fields_extracted = len([v for v in extracted_fields.values() if v is not None and v != ''])
        total_expected_fields = self._get_expected_fields_count(document_type)
        fields_missing = max(0, total_expected_fields - fields_extracted)
        
        # Calculate accuracy (if manual verification provided)
        accuracy_score = 1.0
        if manual_verification_result:
            accuracy_score = self._calculate_accuracy(extracted_fields, manual_verification_result)
        else:
            # Estimate accuracy based on confidence and completeness
            completeness = fields_extracted / total_expected_fields if total_expected_fields > 0 else 0
            accuracy_score = (confidence + completeness) / 2
        
        # Calculate cost estimate
        cost_estimate = self._calculate_cost(document_type, process_type, processing_time)
        
        # Determine if human review required
        human_review_required = (
            confidence < 0.8 or 
            status in [ValidationStatus.PARTIAL, ValidationStatus.NEEDS_REVIEW] or
            fields_missing > 2
        )
        
        # Extract errors and warnings
        errors = validation_result.get('validation_details', {}).get('errors', [])
        warnings = validation_result.get('validation_details', {}).get('warnings', [])
        
        metrics = ValidationMetrics(
            document_type=document_type,
            process_type=process_type,
            start_time=datetime.now() - timedelta(seconds=processing_time),
            end_time=datetime.now(),
            processing_time_seconds=processing_time,
            validation_status=status,
            confidence_score=confidence,
            fields_extracted=fields_extracted,
            fields_missing=fields_missing,
            accuracy_score=accuracy_score,
            cost_estimate=cost_estimate,
            human_review_required=human_review_required,
            errors_found=errors,
            warnings_found=warnings
        )
        
        self.metrics_data.append(metrics)
        return metrics
    
    def _get_expected_fields_count(self, document_type: str) -> int:
        """Get expected field count untuk document type"""
        field_counts = {
            "ktp": 10,  # NIK, Nama, Tempat Lahir, Tanggal Lahir, Jenis Kelamin, Alamat, Agama, Status, Pekerjaan, Kewarganegaraan
            "akta": 11,  # Nomor Akta, Tanggal, Notaris, Perusahaan, Modal, Alamat, Direktur, Komisaris, Bidang Usaha, NPWP, Modal Disetor
            "comprehensive": 21
        }
        return field_counts.get(document_type.lower(), 5)
    
    def _calculate_accuracy(self, extracted_fields: Dict, manual_result: Dict) -> float:
        """Calculate accuracy berdasarkan manual verification"""
        if not manual_result:
            return 0.0
        
        correct_fields = 0
        total_fields = 0
        
        for field, ai_value in extracted_fields.items():
            if field in manual_result:
                total_fields += 1
                manual_value = manual_result[field]
                
                # Simple similarity check
                if ai_value and manual_value:
                    ai_clean = str(ai_value).strip().lower()
                    manual_clean = str(manual_value).strip().lower()
                    
                    if ai_clean == manual_clean:
                        correct_fields += 1
                    elif self._similarity_check(ai_clean, manual_clean) > 0.8:
                        correct_fields += 0.8  # Partial credit
        
        return correct_fields / total_fields if total_fields > 0 else 0.0
    
    def _similarity_check(self, str1: str, str2: str) -> float:
        """Simple similarity check for strings"""
        if not str1 or not str2:
            return 0.0
        
        # Jaccard similarity
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_cost(self, document_type: str, process_type: ProcessType, processing_time: float) -> float:
        """Calculate estimated cost in IDR"""
        if process_type == ProcessType.MANUAL:
            return self.manual_baseline["cost_per_verification_idr"].get(document_type.lower(), 50000)
        
        elif process_type == ProcessType.AI_AUTOMATED:
            # AI cost calculation
            # Base API costs + infrastructure
            api_cost_per_request = 500  # IDR 500 per API call
            ocr_cost = 300  # IDR 300 for OCR processing
            infrastructure_cost = 100  # IDR 100 for compute
            
            return api_cost_per_request + ocr_cost + infrastructure_cost
        
        else:  # HYBRID
            ai_cost = self._calculate_cost(document_type, ProcessType.AI_AUTOMATED, processing_time)
            manual_cost = self.manual_baseline["cost_per_verification_idr"].get(document_type.lower(), 50000)
            return ai_cost + (manual_cost * 0.3)  # 30% manual review cost
    
    def generate_comparison_report(self, document_type: str = None) -> Dict:
        """Generate comprehensive comparison report"""
        
        # Filter data by document type if specified
        filtered_data = self.metrics_data
        if document_type:
            filtered_data = [m for m in self.metrics_data if m.document_type.lower() == document_type.lower()]
        
        if not filtered_data:
            return {"error": "No data available for comparison"}
        
        # Separate AI and Manual metrics
        ai_metrics = [m for m in filtered_data if m.process_type == ProcessType.AI_AUTOMATED]
        manual_metrics = [m for m in filtered_data if m.process_type == ProcessType.MANUAL]
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "document_type": document_type or "all",
            "data_points": {
                "ai_automated": len(ai_metrics),
                "manual": len(manual_metrics),
                "total": len(filtered_data)
            },
            "performance_comparison": self._compare_performance(ai_metrics, manual_metrics),
            "cost_analysis": self._analyze_costs(ai_metrics, manual_metrics),
            "quality_metrics": self._analyze_quality(ai_metrics, manual_metrics),
            "efficiency_metrics": self._analyze_efficiency(ai_metrics, manual_metrics),
            "recommendations": self._generate_recommendations(ai_metrics, manual_metrics),
            "roi_analysis": self._calculate_roi(ai_metrics, manual_metrics)
        }
        
        return report
    
    def _compare_performance(self, ai_metrics: List[ValidationMetrics], manual_metrics: List[ValidationMetrics]) -> Dict:
        """Compare performance metrics"""
        if not ai_metrics:
            return {"error": "No AI metrics available"}
        
        ai_times = [m.processing_time_seconds for m in ai_metrics]
        ai_accuracy = [m.accuracy_score for m in ai_metrics]
        ai_confidence = [m.confidence_score for m in ai_metrics]
        
        # Use baseline for manual if no actual manual data
        if not manual_metrics:
            # Get document type from AI metrics
            doc_type = ai_metrics[0].document_type.lower()
            manual_time_minutes = self.manual_baseline["average_processing_time_minutes"].get(doc_type, 15)
            manual_accuracy = self.manual_baseline["accuracy_rate"].get(doc_type, 0.9)
            
            manual_comparison = {
                "average_time_seconds": manual_time_minutes * 60,
                "average_accuracy": manual_accuracy,
                "data_source": "baseline_estimate"
            }
        else:
            manual_times = [m.processing_time_seconds for m in manual_metrics]
            manual_accuracy = [m.accuracy_score for m in manual_metrics]
            
            manual_comparison = {
                "average_time_seconds": statistics.mean(manual_times),
                "average_accuracy": statistics.mean(manual_accuracy),
                "data_source": "actual_data"
            }
        
        ai_avg_time = statistics.mean(ai_times)
        ai_avg_accuracy = statistics.mean(ai_accuracy)
        
        return {
            "ai_automated": {
                "average_time_seconds": ai_avg_time,
                "average_accuracy": ai_avg_accuracy,
                "average_confidence": statistics.mean(ai_confidence),
                "median_time_seconds": statistics.median(ai_times),
                "std_dev_time": statistics.stdev(ai_times) if len(ai_times) > 1 else 0
            },
            "manual": manual_comparison,
            "improvement_factors": {
                "speed_improvement": manual_comparison["average_time_seconds"] / ai_avg_time,
                "accuracy_improvement": ai_avg_accuracy / manual_comparison["average_accuracy"],
                "time_saved_percentage": ((manual_comparison["average_time_seconds"] - ai_avg_time) / manual_comparison["average_time_seconds"]) * 100
            }
        }
    
    def _analyze_costs(self, ai_metrics: List[ValidationMetrics], manual_metrics: List[ValidationMetrics]) -> Dict:
        """Analyze cost comparison"""
        if not ai_metrics:
            return {"error": "No AI metrics available"}
        
        ai_costs = [m.cost_estimate for m in ai_metrics]
        ai_avg_cost = statistics.mean(ai_costs)
        
        # Get manual cost baseline
        doc_type = ai_metrics[0].document_type.lower()
        manual_avg_cost = self.manual_baseline["cost_per_verification_idr"].get(doc_type, 50000)
        
        return {
            "ai_automated": {
                "average_cost_idr": ai_avg_cost,
                "median_cost_idr": statistics.median(ai_costs),
                "total_cost_idr": sum(ai_costs)
            },
            "manual": {
                "average_cost_idr": manual_avg_cost,
                "total_cost_idr": manual_avg_cost * len(ai_metrics)  # For same number of validations
            },
            "cost_savings": {
                "savings_per_validation_idr": manual_avg_cost - ai_avg_cost,
                "savings_percentage": ((manual_avg_cost - ai_avg_cost) / manual_avg_cost) * 100,
                "total_savings_idr": (manual_avg_cost - ai_avg_cost) * len(ai_metrics)
            }
        }
    
    def _analyze_quality(self, ai_metrics: List[ValidationMetrics], manual_metrics: List[ValidationMetrics]) -> Dict:
        """Analyze quality metrics"""
        if not ai_metrics:
            return {"error": "No AI metrics available"}
        
        # AI Quality Analysis
        ai_valid_count = len([m for m in ai_metrics if m.validation_status == ValidationStatus.VALID])
        ai_review_required = len([m for m in ai_metrics if m.human_review_required])
        ai_error_rate = len([m for m in ai_metrics if len(m.errors_found) > 0]) / len(ai_metrics)
        
        # Manual baseline
        doc_type = ai_metrics[0].document_type.lower()
        manual_error_rate = self.manual_baseline["error_rate"].get(doc_type, 0.1)
        
        return {
            "ai_automated": {
                "success_rate": ai_valid_count / len(ai_metrics),
                "human_review_rate": ai_review_required / len(ai_metrics),
                "error_rate": ai_error_rate,
                "average_fields_extracted": statistics.mean([m.fields_extracted for m in ai_metrics])
            },
            "manual": {
                "success_rate": 1 - manual_error_rate,
                "error_rate": manual_error_rate,
                "human_review_rate": 1.0  # Manual always requires human
            },
            "quality_improvement": {
                "error_reduction": ((manual_error_rate - ai_error_rate) / manual_error_rate) * 100,
                "automation_rate": (1 - (ai_review_required / len(ai_metrics))) * 100
            }
        }
    
    def _analyze_efficiency(self, ai_metrics: List[ValidationMetrics], manual_metrics: List[ValidationMetrics]) -> Dict:
        """Analyze efficiency metrics"""
        if not ai_metrics:
            return {"error": "No AI metrics available"}
        
        # Calculate throughput (validations per hour)
        ai_avg_time = statistics.mean([m.processing_time_seconds for m in ai_metrics])
        ai_throughput_per_hour = 3600 / ai_avg_time
        
        doc_type = ai_metrics[0].document_type.lower()
        manual_time_minutes = self.manual_baseline["average_processing_time_minutes"].get(doc_type, 15)
        manual_throughput_per_hour = 60 / manual_time_minutes
        
        return {
            "throughput_analysis": {
                "ai_validations_per_hour": ai_throughput_per_hour,
                "manual_validations_per_hour": manual_throughput_per_hour,
                "throughput_improvement": ai_throughput_per_hour / manual_throughput_per_hour
            },
            "scalability": {
                "ai_scalability_factor": "unlimited",  # Can scale horizontally
                "manual_scalability_factor": 1.0,  # Limited by human resources
                "concurrent_processing": "Yes" if len(ai_metrics) > 0 else "No"
            },
            "availability": {
                "ai_uptime": "24/7",
                "manual_uptime": "8 hours/day (business hours)",
                "availability_improvement": 3.0  # 24/7 vs 8 hours
            }
        }
    
    def _generate_recommendations(self, ai_metrics: List[ValidationMetrics], manual_metrics: List[ValidationMetrics]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if not ai_metrics:
            return ["No AI metrics available for analysis"]
        
        # Analyze patterns
        avg_confidence = statistics.mean([m.confidence_score for m in ai_metrics])
        review_rate = len([m for m in ai_metrics if m.human_review_required]) / len(ai_metrics)
        
        if avg_confidence > 0.9:
            recommendations.append("AI confidence is excellent (>90%). Consider reducing human review thresholds.")
        elif avg_confidence < 0.7:
            recommendations.append("AI confidence is low (<70%). Consider improving training data or model parameters.")
        
        if review_rate > 0.3:
            recommendations.append("High human review rate (>30%). Focus on improving field extraction accuracy.")
        elif review_rate < 0.1:
            recommendations.append("Low human review rate (<10%). AI system is performing excellently with minimal human intervention.")
        
        # Cost analysis
        ai_avg_cost = statistics.mean([m.cost_estimate for m in ai_metrics])
        doc_type = ai_metrics[0].document_type.lower()
        manual_cost = self.manual_baseline["cost_per_verification_idr"].get(doc_type, 50000)
        
        if ai_avg_cost < manual_cost * 0.2:
            recommendations.append(f"Excellent cost efficiency: AI costs are {((manual_cost - ai_avg_cost) / manual_cost) * 100:.1f}% lower than manual.")
        
        recommendations.append("Implement hybrid approach: AI for initial processing, human review for edge cases.")
        recommendations.append("Set up continuous monitoring for accuracy and cost optimization.")
        
        return recommendations
    
    def _calculate_roi(self, ai_metrics: List[ValidationMetrics], manual_metrics: List[ValidationMetrics]) -> Dict:
        """Calculate Return on Investment"""
        if not ai_metrics:
            return {"error": "No AI metrics available"}
        
        # Monthly processing volume (estimate)
        monthly_volume = 1000  # Assume 1000 validations per month
        
        # Cost calculations
        ai_avg_cost = statistics.mean([m.cost_estimate for m in ai_metrics])
        doc_type = ai_metrics[0].document_type.lower()
        manual_avg_cost = self.manual_baseline["cost_per_verification_idr"].get(doc_type, 50000)
        
        monthly_ai_cost = ai_avg_cost * monthly_volume
        monthly_manual_cost = manual_avg_cost * monthly_volume
        monthly_savings = monthly_manual_cost - monthly_ai_cost
        
        # Implementation cost estimate
        implementation_cost = 50000000  # IDR 50 million for AI implementation
        
        # Time to break even
        break_even_months = implementation_cost / monthly_savings if monthly_savings > 0 else float('inf')
        
        # Annual projections
        annual_savings = monthly_savings * 12
        annual_roi = (annual_savings / implementation_cost) * 100 if implementation_cost > 0 else 0
        
        return {
            "monthly_analysis": {
                "volume_assumption": monthly_volume,
                "ai_monthly_cost_idr": monthly_ai_cost,
                "manual_monthly_cost_idr": monthly_manual_cost,
                "monthly_savings_idr": monthly_savings
            },
            "investment_analysis": {
                "implementation_cost_idr": implementation_cost,
                "break_even_months": round(break_even_months, 1) if break_even_months != float('inf') else "Never",
                "annual_savings_idr": annual_savings,
                "annual_roi_percentage": round(annual_roi, 2)
            },
            "3_year_projection": {
                "total_savings_idr": annual_savings * 3,
                "net_benefit_idr": (annual_savings * 3) - implementation_cost,
                "roi_3_year_percentage": (((annual_savings * 3) - implementation_cost) / implementation_cost) * 100
            }
        }
    
    def export_metrics(self, filename: str = None) -> str:
        """Export metrics to JSON file"""
        if not filename:
            filename = f"ekyc_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert dataclass to dict for JSON serialization
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_validations": len(self.metrics_data),
            "manual_baseline": self.manual_baseline,
            "metrics": []
        }
        
        for metric in self.metrics_data:
            export_data["metrics"].append({
                "document_type": metric.document_type,
                "process_type": metric.process_type.value,
                "start_time": metric.start_time.isoformat(),
                "end_time": metric.end_time.isoformat(),
                "processing_time_seconds": metric.processing_time_seconds,
                "validation_status": metric.validation_status.value,
                "confidence_score": metric.confidence_score,
                "fields_extracted": metric.fields_extracted,
                "fields_missing": metric.fields_missing,
                "accuracy_score": metric.accuracy_score,
                "cost_estimate": metric.cost_estimate,
                "human_review_required": metric.human_review_required,
                "errors_found": metric.errors_found,
                "warnings_found": metric.warnings_found
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename
