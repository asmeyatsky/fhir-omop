-- OMOP CDM v5.4 Schema — Phase 1 Tables
-- Tables: person, visit_occurrence, condition_occurrence, measurement, observation
-- Plus supporting tables: location, care_site, provider
-- Reference: https://ohdsi.github.io/CommonDataModel/cdm54.html

-- ============================================================
-- LOCATION
-- ============================================================
CREATE TABLE IF NOT EXISTS location (
    location_id         BIGINT PRIMARY KEY,
    address_1           VARCHAR(255),
    address_2           VARCHAR(255),
    city                VARCHAR(255),
    state               VARCHAR(50),
    zip                 VARCHAR(20),
    county              VARCHAR(255),
    country             VARCHAR(100),
    location_source_value VARCHAR(255),
    country_concept_id  INTEGER,
    country_source_value VARCHAR(100),
    latitude            NUMERIC,
    longitude           NUMERIC
);

-- ============================================================
-- CARE_SITE
-- ============================================================
CREATE TABLE IF NOT EXISTS care_site (
    care_site_id                BIGINT PRIMARY KEY,
    care_site_name              VARCHAR(500),
    place_of_service_concept_id INTEGER,
    location_id                 BIGINT,
    care_site_source_value      VARCHAR(255),
    place_of_service_source_value VARCHAR(255)
);

-- ============================================================
-- PROVIDER
-- ============================================================
CREATE TABLE IF NOT EXISTS provider (
    provider_id                 BIGINT PRIMARY KEY,
    provider_name               VARCHAR(500),
    npi                         VARCHAR(50),
    dea                         VARCHAR(50),
    specialty_concept_id        INTEGER,
    care_site_id                BIGINT,
    year_of_birth               INTEGER,
    gender_concept_id           INTEGER,
    provider_source_value       VARCHAR(255),
    specialty_source_value      VARCHAR(255),
    specialty_source_concept_id INTEGER,
    gender_source_value         VARCHAR(50),
    gender_source_concept_id    INTEGER
);

-- ============================================================
-- PERSON
-- ============================================================
CREATE TABLE IF NOT EXISTS person (
    person_id                   BIGSERIAL PRIMARY KEY,
    gender_concept_id           INTEGER NOT NULL,
    year_of_birth               INTEGER NOT NULL,
    month_of_birth              INTEGER,
    day_of_birth                INTEGER,
    birth_datetime              TIMESTAMP,
    race_concept_id             INTEGER NOT NULL,
    ethnicity_concept_id        INTEGER NOT NULL,
    location_id                 BIGINT,
    provider_id                 BIGINT,
    care_site_id                BIGINT,
    person_source_value         VARCHAR(255),
    gender_source_value         VARCHAR(50),
    gender_source_concept_id    INTEGER,
    race_source_value           VARCHAR(255),
    race_source_concept_id      INTEGER,
    ethnicity_source_value      VARCHAR(255),
    ethnicity_source_concept_id INTEGER
);

-- ============================================================
-- VISIT_OCCURRENCE
-- ============================================================
CREATE TABLE IF NOT EXISTS visit_occurrence (
    visit_occurrence_id         BIGSERIAL PRIMARY KEY,
    person_id                   BIGINT NOT NULL,
    visit_concept_id            INTEGER NOT NULL,
    visit_start_date            DATE NOT NULL,
    visit_start_datetime        TIMESTAMP,
    visit_end_date              DATE,
    visit_end_datetime          TIMESTAMP,
    visit_type_concept_id       INTEGER NOT NULL,
    provider_id                 BIGINT,
    care_site_id                BIGINT,
    visit_source_value          VARCHAR(255),
    visit_source_concept_id     INTEGER,
    admitted_from_concept_id    INTEGER,
    admitted_from_source_value  VARCHAR(255),
    discharged_to_concept_id    INTEGER,
    discharged_to_source_value  VARCHAR(255),
    preceding_visit_occurrence_id BIGINT
);

-- ============================================================
-- CONDITION_OCCURRENCE
-- ============================================================
CREATE TABLE IF NOT EXISTS condition_occurrence (
    condition_occurrence_id     BIGSERIAL PRIMARY KEY,
    person_id                   BIGINT NOT NULL,
    condition_concept_id        INTEGER NOT NULL,
    condition_start_date        DATE NOT NULL,
    condition_start_datetime    TIMESTAMP,
    condition_end_date          DATE,
    condition_end_datetime      TIMESTAMP,
    condition_type_concept_id   INTEGER NOT NULL,
    condition_status_concept_id INTEGER,
    stop_reason                 VARCHAR(255),
    provider_id                 BIGINT,
    visit_occurrence_id         BIGINT,
    visit_detail_id             BIGINT,
    condition_source_value      VARCHAR(255),
    condition_source_concept_id INTEGER,
    condition_status_source_value VARCHAR(255)
);

-- ============================================================
-- MEASUREMENT
-- ============================================================
CREATE TABLE IF NOT EXISTS measurement (
    measurement_id              BIGSERIAL PRIMARY KEY,
    person_id                   BIGINT NOT NULL,
    measurement_concept_id      INTEGER NOT NULL,
    measurement_date            DATE NOT NULL,
    measurement_datetime        TIMESTAMP,
    measurement_time            VARCHAR(20),
    measurement_type_concept_id INTEGER NOT NULL,
    operator_concept_id         INTEGER,
    value_as_number             NUMERIC,
    value_as_concept_id         INTEGER,
    unit_concept_id             INTEGER,
    range_low                   NUMERIC,
    range_high                  NUMERIC,
    provider_id                 BIGINT,
    visit_occurrence_id         BIGINT,
    visit_detail_id             BIGINT,
    measurement_source_value    VARCHAR(255),
    measurement_source_concept_id INTEGER,
    unit_source_value           VARCHAR(100),
    unit_source_concept_id      INTEGER,
    value_source_value          VARCHAR(255),
    measurement_event_id        BIGINT,
    meas_event_field_concept_id INTEGER
);

-- ============================================================
-- OBSERVATION
-- ============================================================
CREATE TABLE IF NOT EXISTS observation (
    observation_id              BIGSERIAL PRIMARY KEY,
    person_id                   BIGINT NOT NULL,
    observation_concept_id      INTEGER NOT NULL,
    observation_date            DATE NOT NULL,
    observation_datetime        TIMESTAMP,
    observation_type_concept_id INTEGER NOT NULL,
    value_as_number             NUMERIC,
    value_as_string             VARCHAR(1000),
    value_as_concept_id         INTEGER,
    qualifier_concept_id        INTEGER,
    unit_concept_id             INTEGER,
    provider_id                 BIGINT,
    visit_occurrence_id         BIGINT,
    visit_detail_id             BIGINT,
    observation_source_value    VARCHAR(255),
    observation_source_concept_id INTEGER,
    unit_source_value           VARCHAR(100),
    qualifier_source_value      VARCHAR(255),
    value_source_value          VARCHAR(255),
    observation_event_id        BIGINT,
    obs_event_field_concept_id  INTEGER
);

-- ============================================================
-- INDEXES for query performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_person_source ON person (person_source_value);
CREATE INDEX IF NOT EXISTS idx_visit_person ON visit_occurrence (person_id);
CREATE INDEX IF NOT EXISTS idx_visit_source ON visit_occurrence (visit_source_value);
CREATE INDEX IF NOT EXISTS idx_condition_person ON condition_occurrence (person_id);
CREATE INDEX IF NOT EXISTS idx_measurement_person ON measurement (person_id);
CREATE INDEX IF NOT EXISTS idx_observation_person ON observation (person_id);
