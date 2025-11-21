# Implementation and Evaluation of OWASP LLM Security Mitigations in Multi-Agent Systems: A Design Science Approach

**Author**: Md Sadidur Rahman
**Institution**: Tampere University
**Faculty**: Information Technology and Communication Sciences
**Degree**: Master of Science Thesis
**Examiners**: José Antonio Siqueira de Cerqueira, Kai-Kristian Kemell
**Date**: December 2025

---

## Abstract

Large Language Model (LLM) applications have rapidly transitioned from experimental prototypes to mission-critical systems handling sensitive data and autonomous decision-making across healthcare, finance, and enterprise domains. However, this deployment acceleration has outpaced the development of validated security mechanisms, creating critical vulnerabilities that traditional software security frameworks fail to address. Recent high-profile incidents, including the compromise of OpenAI's ChatGPT Atlas browser within 24 hours of launch and Google Gemini's data leakage through malicious calendar invitations, underscore the urgent need for systematic security implementations in production LLM systems.

This thesis addresses three fundamental gaps in current LLM application security: the implementation gap between OWASP security guidelines and production systems, the multi-agent security gap where coordinated agent interactions introduce novel attack vectors, and the evaluation gap where rigorous quantitative security assessment remains limited. We employ Design Science Research methodology to systematically implement and evaluate OWASP LLM security mitigations for four critical vulnerabilities: prompt injection (LLM01), sensitive information disclosure (LLM02), excessive agency (LLM06), and misinformation (LLM09) within a multi-agent architecture.

Our implementation, the Finnish Politician Analysis System (FPAS), demonstrates a four-layer defense-in-depth security architecture that transparently integrates security controls without requiring fundamental agent redesign. The system processes 541 Finnish politicians and 2,847 news articles through coordinated query and analysis agents protected by a Prompt Guard (pattern-based injection detection), Output Sanitizer (credential redaction), Agent Permission Manager (granular tool access control), Excessive Agency Monitor (anomaly detection), and Verification System (fact-checking with source attribution).

Through systematic adversarial testing across 50 attack scenarios, we demonstrate that comprehensive OWASP mitigation reduces attack success rates by 74% (from 86% baseline to 12% with full security controls) while introducing minimal performance overhead (median 47ms latency increase, representing 15% overhead). Our evaluation reveals that defense-in-depth architectures provide significantly stronger protection than vendor-level controls alone (12% vs. 38% attack success), validating the necessity of application-layer security mechanisms.

This research makes four contributions to LLM application security. First, we provide the first systematic implementation of four OWASP LLM 2025 categories in a production-grade multi-agent system, validated through 141 unit and integration tests achieving 96% coverage on security-critical components. Second, we establish a quantitative evaluation framework enabling reproducible security assessment through documented attack scenarios, standardized metrics, and statistical comparison across security configurations. Third, we characterize multi-agent-specific threats including agent-to-agent prompt injection, workflow-based permission escalation, and cascading misinformation propagation, extending OWASP's single-agent threat model. Fourth, we document reusable architectural patterns for decorator-based security injection, agent isolation boundaries, and orchestration-layer enforcement that practitioners can integrate into existing LLM applications.

Our findings demonstrate that systematic OWASP mitigation is both technically feasible and empirically effective in multi-agent contexts, providing evidence-based guidance for securing LLM applications in production environments.

**Keywords**: Large Language Models, OWASP Top 10, Multi-Agent Systems, LLM Security, Prompt Injection, Excessive Agency, Design Science Research, LangChain, Application Security

---

## Acknowledgements

This thesis would not have been possible without the support and guidance of several individuals and organizations.

I extend my deepest gratitude to my supervisor, **José Antonio Siqueira de Cerqueira**, whose expertise in AI security and unwavering support throughout this research has been invaluable. His insightful feedback and encouragement significantly shaped this work. I also thank **Kai-Kristian Kemell** for serving as examiner and providing critical perspectives that strengthened the research methodology.

My sincere appreciation goes to **Professor Pekka Abrahamsson** and the **GPT-Lab research group** at Tampere University for creating an intellectually stimulating environment that fostered this research. The GPT-Lab's commitment to bridging empirical research with real-world AI applications provided the perfect context for exploring practical security implementations.

I am grateful to the **Finnish Parliament (Eduskunta)** and **Statistics Finland** for providing open access to political data that enabled this research, demonstrating the power of open data initiatives for advancing academic research. I also acknowledge **OpenAI** for API access that made the empirical evaluation possible.

Special thanks to my family for their patience and unwavering support during the intensive periods of this thesis work. Their understanding and encouragement sustained me through challenging moments.

Finally, I dedicate this work to all practitioners working to secure AI systems in production environments. May this research contribute to safer, more trustworthy deployment of AI technologies that benefit society.

---

