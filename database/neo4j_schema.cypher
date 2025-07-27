// =============================================================================
// FINNISH POLITICIAN ANALYSIS SYSTEM - OPTIMIZED NEO4J SCHEMA
// Senior-Level Graph Database Design for Maximum Political Analysis Value
// =============================================================================

// =============================================================================
// 1. CONSTRAINTS - Data Integrity & Uniqueness
// =============================================================================

// Core Entity Constraints
CREATE CONSTRAINT politician_id_unique IF NOT EXISTS FOR (p:Politician) REQUIRE p.politician_id IS UNIQUE;
CREATE CONSTRAINT party_id_unique IF NOT EXISTS FOR (party:Party) REQUIRE party.party_id IS UNIQUE;
CREATE CONSTRAINT article_id_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.article_id IS UNIQUE;
CREATE CONSTRAINT position_id_unique IF NOT EXISTS FOR (pos:Position) REQUIRE pos.position_id IS UNIQUE;
CREATE CONSTRAINT constituency_id_unique IF NOT EXISTS FOR (c:Constituency) REQUIRE c.constituency_id IS UNIQUE;
CREATE CONSTRAINT policy_topic_id_unique IF NOT EXISTS FOR (pt:PolicyTopic) REQUIRE pt.topic_id IS UNIQUE;
CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE;

// Business Logic Constraints
CREATE CONSTRAINT politician_name_party_unique IF NOT EXISTS FOR (p:Politician) REQUIRE (p.name, p.current_party) IS UNIQUE;
CREATE CONSTRAINT article_url_unique IF NOT EXISTS FOR (a:Article) REQUIRE a.url IS UNIQUE;

// =============================================================================
// 2. PERFORMANCE INDEXES - Optimized for Finnish Political Queries
// =============================================================================

// Politician Analysis Indexes
CREATE INDEX politician_name_fulltext IF NOT EXISTS FOR (p:Politician) ON (p.name);
CREATE INDEX politician_party_index IF NOT EXISTS FOR (p:Politician) ON (p.current_party);
CREATE INDEX politician_constituency_index IF NOT EXISTS FOR (p:Politician) ON (p.constituency);
CREATE INDEX politician_position_index IF NOT EXISTS FOR (p:Politician) ON (p.current_position);
CREATE INDEX politician_active_index IF NOT EXISTS FOR (p:Politician) ON (p.is_active);
CREATE INDEX politician_term_index IF NOT EXISTS FOR (p:Politician) ON (p.current_term_start, p.current_term_end);

// News & Media Analysis Indexes
CREATE INDEX article_published_date_index IF NOT EXISTS FOR (a:Article) ON (a.published_date);
CREATE INDEX article_source_index IF NOT EXISTS FOR (a:Article) ON (a.source);
CREATE INDEX article_sentiment_index IF NOT EXISTS FOR (a:Article) ON (a.sentiment_score);
CREATE INDEX article_political_relevance_index IF NOT EXISTS FOR (a:Article) ON (a.political_relevance);
CREATE INDEX article_title_fulltext IF NOT EXISTS FOR (a:Article) ON (a.title);

// Political Network Indexes
CREATE INDEX party_coalition_index IF NOT EXISTS FOR (party:Party) ON (party.coalition_status);
CREATE INDEX party_ideology_index IF NOT EXISTS FOR (party:Party) ON (party.ideology_score);
CREATE INDEX position_hierarchy_index IF NOT EXISTS FOR (pos:Position) ON (pos.hierarchy_level);

// Temporal Analysis Indexes
CREATE INDEX event_date_index IF NOT EXISTS FOR (e:Event) ON (e.event_date);
CREATE INDEX event_type_index IF NOT EXISTS FOR (e:Event) ON (e.event_type);

// =============================================================================
// 3. CORE ENTITY NODES - Rich Data Model
// =============================================================================

// Politicians - Comprehensive Profile
// Properties: politician_id, name, first_name, last_name, date_of_birth, 
//            current_party, previous_parties[], current_position, previous_positions[],
//            constituency, education[], career_background[], contact_info{},
//            social_media{}, is_active, current_term_start, current_term_end,
//            biography, political_alignment, committee_memberships[],
//            voting_record_summary{}, media_mentions_count, influence_score,
//            created_at, updated_at, data_sources[]

// Political Parties - Organizational Structure
// Properties: party_id, name, short_name, founded_date, ideology_score, 
//            coalition_status, current_leader, member_count, parliamentary_seats,
//            regional_strength{}, policy_positions{}, historical_performance[],
//            website, headquarters_address, contact_info{}, is_active,
//            created_at, updated_at

// News Articles - Media Analysis
// Properties: article_id, title, content, summary, author, source, published_date,
//            url, language, word_count, sentiment_score, political_relevance,
//            mentioned_politicians[], mentioned_parties[], policy_topics[],
//            article_type, section, tags[], social_shares, comments_count,
//            credibility_score, bias_score, created_at, updated_at

// Government Positions - Hierarchical Roles
// Properties: position_id, title, department, hierarchy_level, responsibilities[],
//            appointment_process, term_length, salary_grade, is_elected,
//            required_qualifications[], historical_holders[], is_active,
//            created_at, updated_at

// Constituencies - Electoral Geography
// Properties: constituency_id, name, region, population, voter_turnout_history[],
//            demographic_profile{}, economic_indicators{}, political_leaning,
//            area_km2, municipalities[], electoral_history[], is_active,
//            created_at, updated_at

// Policy Topics - Issue Tracking
// Properties: topic_id, name, category, description, importance_score,
//            related_legislation[], public_opinion_trend[], media_coverage_trend[],
//            stakeholder_positions{}, is_active, created_at, updated_at

// Political Events - Temporal Context
// Properties: event_id, title, description, event_type, event_date, location,
//            participants[], outcomes[], media_coverage, significance_score,
//            related_topics[], created_at, updated_at

// =============================================================================
// 4. STRATEGIC RELATIONSHIPS - Political Network Analysis
// =============================================================================

// Core Political Relationships
// (:Politician)-[:MEMBER_OF {start_date, end_date, role, is_current}]->(:Party)
// (:Politician)-[:REPRESENTS {start_date, end_date, vote_share, is_current}]->(:Constituency)
// (:Politician)-[:HOLDS_POSITION {start_date, end_date, appointment_method, is_current}]->(:Position)
// (:Politician)-[:EDUCATED_AT {degree, graduation_year, field_of_study}]->(:Institution)

// Political Network Relationships
// (:Politician)-[:COLLABORATES_WITH {frequency, strength, policy_areas[], last_collaboration}]->(:Politician)
// (:Politician)-[:OPPOSES {frequency, strength, policy_areas[], last_opposition}]->(:Politician)
// (:Politician)-[:MENTORS {start_date, relationship_type}]->(:Politician)
// (:Politician)-[:SUCCEEDED {position, transition_date}]->(:Politician)

// Party & Coalition Relationships
// (:Party)-[:COALITION_WITH {start_date, end_date, coalition_name, is_current}]->(:Party)
// (:Party)-[:SPLIT_FROM {split_date, reason, key_figures[]}]->(:Party)
// (:Party)-[:MERGED_WITH {merge_date, new_party_name}]->(:Party)

// Media & Public Opinion Relationships
// (:Article)-[:MENTIONS {sentiment, prominence, context}]->(:Politician)
// (:Article)-[:DISCUSSES {stance, depth, bias_indicator}]->(:PolicyTopic)
// (:Article)-[:COVERS {coverage_type, prominence}]->(:Event)

// Policy & Voting Relationships
// (:Politician)-[:SUPPORTS_POLICY {strength, public_statement_date, voting_record}]->(:PolicyTopic)
// (:Politician)-[:OPPOSES_POLICY {strength, public_statement_date, voting_record}]->(:PolicyTopic)
// (:Politician)-[:VOTED_ON {vote, date, bill_name}]->(:Legislation)

// Influence & Network Relationships
// (:Politician)-[:INFLUENCES {influence_type, strength, evidence[]}]->(:Politician)
// (:Politician)-[:ADVISED_BY {role, start_date, end_date}]->(:Advisor)
// (:Politician)-[:ENDORSED_BY {endorsement_date, endorsement_type}]->(:Organization)

// =============================================================================
// 5. ADVANCED ANALYTICS VIEWS - Optimized Queries
// =============================================================================

// Political Network Analysis Queries
// 1. Coalition Detection
// MATCH (p1:Politician)-[:COLLABORATES_WITH]-(p2:Politician)
// WHERE p1.current_party <> p2.current_party
// RETURN p1.current_party, p2.current_party, count(*) as cross_party_collaborations
// ORDER BY cross_party_collaborations DESC

// 2. Influence Mapping (Centrality Analysis)
// MATCH (p:Politician)-[r:COLLABORATES_WITH|INFLUENCES]-(other:Politician)
// RETURN p.name, p.current_party, count(r) as connections, 
//        avg(r.strength) as avg_influence_strength
// ORDER BY connections DESC, avg_influence_strength DESC

// 3. Policy Alignment Clustering
// MATCH (p:Politician)-[s:SUPPORTS_POLICY]-(pt:PolicyTopic)
// WITH pt, collect({politician: p.name, party: p.current_party, strength: s.strength}) as supporters
// RETURN pt.name, pt.category, supporters
// ORDER BY size(supporters) DESC

// 4. Media Coverage Analysis
// MATCH (a:Article)-[m:MENTIONS]-(p:Politician)
// WHERE a.published_date >= date() - duration({days: 30})
// RETURN p.name, p.current_party, count(a) as mentions, 
//        avg(m.sentiment) as avg_sentiment, avg(a.political_relevance) as avg_relevance
// ORDER BY mentions DESC

// 5. Temporal Relationship Tracking
// MATCH (p1:Politician)-[r:COLLABORATES_WITH]-(p2:Politician)
// WHERE r.last_collaboration >= date() - duration({months: 6})
// RETURN p1.name, p2.name, r.frequency, r.strength, r.policy_areas
// ORDER BY r.last_collaboration DESC

// =============================================================================
// 6. DATA VALIDATION RULES - Business Logic Constraints
// =============================================================================

// Temporal Consistency Rules
// - Politicians cannot hold multiple positions simultaneously (unless specifically allowed)
// - Party memberships must have valid date ranges
// - Articles must have published_date <= current_date
// - Events must have logical temporal relationships

// Data Quality Rules
// - All entities must have valid data_sources array
// - Sentiment scores must be between -1.0 and 1.0
// - Influence scores must be between 0.0 and 1.0
// - Political relevance scores must be between 0.0 and 1.0

// Relationship Validation Rules
// - Politicians can only represent one constituency at a time
// - Coalition relationships must be mutual
// - Collaboration strength must be supported by evidence

// =============================================================================
// 7. PERFORMANCE OPTIMIZATION HINTS
// =============================================================================

// Query Optimization Tips:
// 1. Always use indexed properties in WHERE clauses
// 2. Limit result sets with appropriate LIMIT clauses
// 3. Use PROFILE/EXPLAIN to analyze query performance
// 4. Consider using APOC procedures for complex analytics
// 5. Implement proper connection pooling for high-throughput scenarios

// Memory Management:
// 1. Use streaming for large result sets
// 2. Implement proper transaction boundaries
// 3. Consider periodic CALL db.stats.retrieve() for monitoring
// 4. Use CALL apoc.periodic.iterate() for batch operations

// =============================================================================
// 8. SECURITY CONSIDERATIONS
// =============================================================================

// Access Control:
// - Implement role-based access control (RBAC)
// - Separate read/write permissions
// - Audit trail for sensitive political data
// - Data anonymization for public APIs

// Data Privacy:
// - GDPR compliance for personal data
// - Data retention policies
// - Secure connection requirements (SSL/TLS)
// - Regular security audits

// =============================================================================
// END OF OPTIMIZED SCHEMA
// =============================================================================
