"""Mock data generation for AI Conversation Analyzer portfolio demo."""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

class MockDataGenerator:
    """Generates realistic mock conversation data for portfolio demonstration."""
    
    def __init__(self):
        self.categories = [
            "technical_development",
            "business_analysis", 
            "ai_ml_research",
            "project_management",
            "system_architecture",
            "data_analytics",
            "strategic_planning",
            "performance_optimization",
            "general"
        ]
        
        self.business_topics = [
            "requirement analysis", "market research", "competitive analysis",
            "stakeholder feedback", "product roadmap", "budget planning",
            "resource allocation", "risk assessment", "ROI analysis"
        ]
        
        self.technical_topics = [
            "API design", "database optimization", "microservices architecture",
            "cloud deployment", "performance tuning", "security implementation",
            "code review", "testing strategy", "CI/CD pipeline"
        ]
        
        self.ai_topics = [
            "model training", "vector embeddings", "semantic search",
            "neural networks", "machine learning", "data preprocessing",
            "model evaluation", "hyperparameter tuning", "feature engineering"
        ]
        
    def generate_conversation_content(self, category: str, length: int = 800) -> str:
        """Generate realistic conversation content for a specific category."""
        
        content_generators = {
            "technical_development": self._generate_technical_content,
            "business_analysis": self._generate_business_content,
            "ai_ml_research": self._generate_ai_ml_content,
            "project_management": self._generate_project_content,
            "system_architecture": self._generate_architecture_content,
            "data_analytics": self._generate_analytics_content,
            "strategic_planning": self._generate_strategy_content,
            "performance_optimization": self._generate_performance_content,
            "general": self._generate_general_content
        }
        
        generator = content_generators.get(category, self._generate_general_content)
        return generator(length)
    
    def _generate_technical_content(self, length: int) -> str:
        """Generate technical development conversation content."""
        technical_phrases = [
            "I've completed the API design analysis and have some recommendations.",
            "The performance metrics show we can achieve significant improvements by restructuring the data flow.",
            "We should implement better error handling mechanisms and add comprehensive logging.",
            "The microservices architecture will provide better scalability and maintainability.",
            "Let's refactor the database queries to optimize performance and reduce latency.",
            "The integration with the external services requires careful handling of rate limits.",
            "We need to implement proper caching strategies to improve response times.",
            "The testing strategy should include unit tests, integration tests, and end-to-end scenarios.",
            "Code review feedback suggests we should simplify the authentication flow.",
            "The deployment pipeline needs automation to reduce manual errors.",
            "Security considerations require implementing proper input validation and sanitization.",
            "The API documentation should be updated to reflect the latest changes."
        ]
        return self._build_content(technical_phrases, length)
    
    def _generate_business_content(self, length: int) -> str:
        """Generate business analysis conversation content."""
        business_phrases = [
            "Based on the stakeholder feedback, we should prioritize features that deliver immediate business value.",
            "The cost-benefit analysis suggests focusing on core functionality first before expanding to advanced features.",
            "Market research indicates strong demand for automation capabilities in our target segment.",
            "ROI projections show positive returns within 18 months if we maintain current development pace.",
            "Competitive analysis reveals opportunities to differentiate through superior user experience.",
            "Resource allocation should balance feature development with technical debt reduction.",
            "Risk assessment highlights the importance of robust data backup and recovery procedures.",
            "Customer feedback emphasizes the need for intuitive interfaces and streamlined workflows.",
            "Budget planning must account for scalability requirements and infrastructure costs.",
            "Strategic partnerships could accelerate market entry and reduce development overhead.",
            "Product roadmap alignment with customer needs is critical for long-term success.",
            "Quality assurance processes should be strengthened to maintain high customer satisfaction."
        ]
        return self._build_content(business_phrases, length)
    
    def _generate_ai_ml_content(self, length: int) -> str:
        """Generate AI/ML research conversation content."""
        ai_phrases = [
            "The vector embedding model shows promising results for semantic similarity tasks.",
            "Model training convergence improved significantly after adjusting the learning rate schedule.",
            "Feature engineering revealed that contextual embeddings outperform static representations.",
            "Cross-validation results demonstrate robust performance across different data distributions.",
            "Hyperparameter tuning using Bayesian optimization yielded 15% improvement in accuracy.",
            "The attention mechanism effectively captures long-range dependencies in conversational data.",
            "Data preprocessing pipeline handles noise and inconsistencies in real-world datasets.",
            "Model evaluation metrics indicate excellent precision and recall for classification tasks.",
            "Transfer learning from pre-trained models reduces training time while maintaining quality.",
            "Ensemble methods combining multiple models improve overall system robustness.",
            "Neural architecture search identified optimal network topology for our specific use case.",
            "Interpretability analysis helps understand model decision-making processes."
        ]
        return self._build_content(ai_phrases, length)
    
    def _generate_project_content(self, length: int) -> str:
        """Generate project management conversation content."""
        project_phrases = [
            "Sprint planning session identified key deliverables for the upcoming development cycle.",
            "Team coordination requires clear communication channels and regular status updates.",
            "Resource dependencies have been mapped and contingency plans are in place.",
            "Timeline adjustments are necessary to accommodate scope changes requested by stakeholders.",
            "Risk mitigation strategies include backup resources and alternative implementation paths.",
            "Quality gates ensure deliverables meet acceptance criteria before moving to next phase.",
            "Cross-functional collaboration is essential for successful project execution.",
            "Progress tracking shows we're on schedule for the major milestone deliverables.",
            "Change management processes help handle evolving requirements efficiently.",
            "Stakeholder engagement ensures alignment between business needs and technical solutions.",
            "Team retrospectives provide valuable insights for continuous process improvement.",
            "Documentation standards maintain knowledge sharing across distributed teams."
        ]
        return self._build_content(project_phrases, length)
    
    def _generate_architecture_content(self, length: int) -> str:
        """Generate system architecture conversation content."""
        architecture_phrases = [
            "The microservices architecture provides excellent scalability and maintainability benefits.",
            "API gateway implementation ensures proper routing, security, and rate limiting capabilities.",
            "Database sharding strategy supports horizontal scaling requirements effectively.",
            "Event-driven architecture enables loose coupling between system components.",
            "Load balancing distributes traffic efficiently across multiple service instances.",
            "Caching layers significantly reduce database load and improve response times.",
            "Service mesh provides observability, security, and traffic management features.",
            "Container orchestration simplifies deployment and resource management processes.",
            "Monitoring and observability tools provide comprehensive system visibility and performance insights.",
            "Disaster recovery procedures ensure business continuity during system failures.",
            "Security architecture implements defense-in-depth principles throughout the stack.",
            "Data architecture supports both transactional and analytical workloads efficiently."
        ]
        return self._build_content(architecture_phrases, length)
    
    def _generate_analytics_content(self, length: int) -> str:
        """Generate data analytics conversation content."""
        analytics_phrases = [
            "Data analysis reveals clear patterns in user behavior and system performance metrics.",
            "Statistical modeling provides insights into key performance indicators and trends.",
            "Reporting dashboard visualizes critical business metrics in real-time.",
            "Data quality assessment identifies inconsistencies requiring attention and correction.",
            "Predictive analytics models forecast future trends with high accuracy rates.",
            "ETL pipeline processing ensures clean, consistent data for analysis workflows.",
            "Business intelligence tools enable self-service analytics for stakeholders.",
            "A/B testing results demonstrate significant improvement in user engagement metrics.",
            "Data warehouse optimization reduces query response times and improves efficiency.",
            "Machine learning models identify anomalies and patterns in large datasets.",
            "Customer segmentation analysis reveals distinct user groups and preferences.",
            "Performance benchmarking shows substantial improvements over previous implementations."
        ]
        return self._build_content(analytics_phrases, length)
    
    def _generate_strategy_content(self, length: int) -> str:
        """Generate strategic planning conversation content."""
        strategy_phrases = [
            "Long-term strategic planning aligns technology investments with business objectives.",
            "Competitive positioning analysis identifies opportunities for market differentiation.",
            "Innovation roadmap balances cutting-edge research with practical implementation needs.",
            "Partnership strategy leverages external expertise to accelerate development timelines.",
            "Market expansion requires careful consideration of regional requirements and regulations.",
            "Digital transformation initiatives modernize legacy systems and processes.",
            "Talent acquisition strategy focuses on critical skills needed for future growth.",
            "Investment priorities reflect both immediate needs and long-term strategic goals.",
            "Change management ensures smooth transition during organizational transformations.",
            "Risk management framework addresses potential challenges and mitigation strategies.",
            "Performance measurement systems track progress toward strategic objectives.",
            "Stakeholder alignment ensures unified direction across all organizational levels."
        ]
        return self._build_content(strategy_phrases, length)
    
    def _generate_performance_content(self, length: int) -> str:
        """Generate performance optimization conversation content."""
        performance_phrases = [
            "Performance profiling identified bottlenecks in database query execution patterns.",
            "Caching implementation reduced average response times by 60% across all endpoints.",
            "Memory optimization strategies eliminated memory leaks and reduced resource consumption.",
            "Database indexing improvements dramatically accelerated complex query performance.",
            "Load testing reveals system capacity limits and scaling requirements.",
            "Code optimization techniques improved throughput while maintaining functionality.",
            "Network optimization reduces latency and improves user experience significantly.",
            "Resource monitoring provides insights into system utilization patterns and trends.",
            "Scalability testing demonstrates system behavior under increasing load conditions.",
            "Performance benchmarking establishes baseline metrics for continuous improvement.",
            "Capacity planning ensures infrastructure can handle projected growth requirements.",
            "Optimization strategies balance performance improvements with code maintainability."
        ]
        return self._build_content(performance_phrases, length)
    
    def _generate_general_content(self, length: int) -> str:
        """Generate general conversation content."""
        general_phrases = [
            "This discussion covers various aspects of project requirements and implementation strategy.",
            "Team collaboration and communication are essential for successful project delivery.",
            "Regular reviews and feedback loops ensure continuous improvement and quality assurance.",
            "Documentation and knowledge sharing facilitate onboarding and team coordination.",
            "Best practices and industry standards guide development and operational procedures.",
            "Continuous learning and skill development keep teams current with evolving technologies.",
            "Process improvement initiatives enhance efficiency and reduce operational overhead.",
            "Quality assurance measures ensure deliverables meet established standards and expectations.",
            "Technical debt management balances new feature development with system maintenance.",
            "Innovation and experimentation drive competitive advantage and market leadership.",
            "Customer focus ensures solutions address real business needs and user requirements.",
            "Agile methodologies enable rapid iteration and responsive development cycles."
        ]
        return self._build_content(general_phrases, length)
    
    def _build_content(self, phrases: List[str], target_length: int) -> str:
        """Build content from phrases to reach target length."""
        content = []
        current_length = 0
        
        while current_length < target_length:
            phrase = random.choice(phrases)
            content.append(phrase)
            current_length += len(phrase) + 1  # +1 for space
        
        return " ".join(content)[:target_length]
    
    def generate_conversation(self) -> Dict[str, Any]:
        """Generate a single realistic conversation."""
        category = random.choice(self.categories)
        
        conversation = {
            "id": str(uuid.uuid4()),
            "title": f"Demo Conversation: {category.replace('_', ' ').title()}",
            "category": category,
            "created_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "message_count": random.randint(5, 25),
            "content": self.generate_conversation_content(category, random.randint(600, 1200)),
            "metadata": {
                "project_name": f"Demo Project {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])}",
                "participants": random.randint(2, 5),
                "complexity_score": round(random.uniform(0.3, 0.9), 2)
            }
        }
        
        return conversation

# Performance benchmark data for portfolio showcase
DEMO_PERFORMANCE_DATA = {
    "processing_metrics": {
        "conversations_per_second": 398.4,
        "total_conversations_processed": 1435,
        "total_chunks_generated": 42157,
        "processing_time_seconds": 3.6,
        "memory_efficiency_mb": 1847,
        "error_rate_percentage": 0.0
    },
    "search_performance": {
        "average_query_time_ms": 45,
        "cache_hit_rate_percentage": 87.5,
        "concurrent_users_supported": 50,
        "search_accuracy_score": 0.94
    },
    "system_reliability": {
        "uptime_percentage": 99.97,
        "availability_sla": 99.9,
        "mean_time_to_recovery_minutes": 2.3,
        "scalability_tested_users": 100
    }
}