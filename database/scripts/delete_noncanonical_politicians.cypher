// Delete all Politician nodes whose ID is not a canonical numeric Eduskunta ID
MATCH (p:Politician)
WHERE NOT p.politician_id =~ '^[0-9]+$'
DETACH DELETE p;
