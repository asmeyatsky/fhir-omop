-- Enterprise Data Classification (NDMO)
-- Classification policies for data governance

CREATE TABLE IF NOT EXISTS classification_policy (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    resource_type   VARCHAR(100),
    field_pattern   VARCHAR(255),
    classification  VARCHAR(50) NOT NULL CHECK (classification IN ('public', 'internal', 'confidential', 'top_secret')),
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Default NDMO classification policies
INSERT INTO classification_policy (name, resource_type, field_pattern, classification, description)
VALUES
    ('Patient Identifiers', 'Patient', 'identifier.*', 'top_secret', 'National IDs, MRNs, passport numbers'),
    ('Patient Contact', 'Patient', 'telecom.*', 'top_secret', 'Phone numbers, email addresses'),
    ('Patient Address', 'Patient', 'address.*', 'top_secret', 'Physical addresses'),
    ('Patient Name', 'Patient', 'name.*', 'top_secret', 'Patient full name, family name'),
    ('Person Source Value', '*', 'person_source_value', 'top_secret', 'OMOP person source value'),
    ('Conditions', 'Condition', '*', 'confidential', 'Diagnosis and condition data'),
    ('Observations', 'Observation', '*', 'confidential', 'Clinical observations and lab results'),
    ('Encounters', 'Encounter', '*', 'confidential', 'Visit and encounter data'),
    ('Admin Metadata', '*', 'meta.*', 'internal', 'Resource metadata'),
    ('Value Sets', 'ValueSet', '*', 'public', 'Terminology value sets'),
    ('Code Systems', 'CodeSystem', '*', 'public', 'Terminology code systems')
ON CONFLICT DO NOTHING;
