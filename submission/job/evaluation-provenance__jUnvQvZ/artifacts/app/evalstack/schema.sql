CREATE SEQUENCE IF NOT EXISTS publication_id_seq;
CREATE SEQUENCE IF NOT EXISTS activation_id_seq;
CREATE SEQUENCE IF NOT EXISTS job_id_seq;
CREATE SEQUENCE IF NOT EXISTS completion_id_seq;

CREATE TABLE IF NOT EXISTS checkpoint_contents (
    checkpoint_content_ref TEXT PRIMARY KEY,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS publications (
    publication_id TEXT PRIMARY KEY,
    publication_seq BIGINT NOT NULL UNIQUE,
    candidate_id TEXT NOT NULL,
    checkpoint_content_ref TEXT NOT NULL REFERENCES checkpoint_contents(checkpoint_content_ref),
    checkpoint_label TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS publications_candidate_order
    ON publications(candidate_id, publication_seq DESC);

CREATE TABLE IF NOT EXISTS contract_contents (
    contract_content_ref TEXT PRIMARY KEY,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS contract_activations (
    activation_id TEXT PRIMARY KEY,
    activation_seq BIGINT NOT NULL UNIQUE,
    contract_content_ref TEXT NOT NULL REFERENCES contract_contents(contract_content_ref),
    contract_label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_seq BIGINT NOT NULL UNIQUE,
    candidate_id TEXT NOT NULL,
    publication_id TEXT NOT NULL REFERENCES publications(publication_id),
    checkpoint_content_ref TEXT NOT NULL REFERENCES checkpoint_contents(checkpoint_content_ref),
    contract_content_ref TEXT NOT NULL REFERENCES contract_contents(contract_content_ref),
    checkpoint_label TEXT NOT NULL,
    contract_label TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'complete')),
    reused BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_checkpoint_content_ref TEXT REFERENCES checkpoint_contents(checkpoint_content_ref),
    resolved_contract_content_ref TEXT REFERENCES contract_contents(contract_content_ref),
    completed_seq BIGINT
);
CREATE INDEX IF NOT EXISTS jobs_candidate_order ON jobs(candidate_id, job_seq DESC);

CREATE TABLE IF NOT EXISTS seed_results (
    checkpoint_content_ref TEXT NOT NULL REFERENCES checkpoint_contents(checkpoint_content_ref),
    contract_content_ref TEXT NOT NULL REFERENCES contract_contents(contract_content_ref),
    seed BIGINT NOT NULL,
    score BIGINT NOT NULL,
    source_job_id TEXT NOT NULL REFERENCES jobs(job_id),
    PRIMARY KEY (checkpoint_content_ref, contract_content_ref, seed)
);

CREATE TABLE IF NOT EXISTS canonical_results (
    checkpoint_content_ref TEXT NOT NULL REFERENCES checkpoint_contents(checkpoint_content_ref),
    contract_content_ref TEXT NOT NULL REFERENCES contract_contents(contract_content_ref),
    score BIGINT NOT NULL,
    seed_count INTEGER NOT NULL,
    completed_by_job_id TEXT NOT NULL REFERENCES jobs(job_id),
    completed_seq BIGINT NOT NULL UNIQUE,
    PRIMARY KEY (checkpoint_content_ref, contract_content_ref)
);

CREATE TABLE IF NOT EXISTS evaluator_calls (
    call_id BIGSERIAL PRIMARY KEY,
    checkpoint_content_ref TEXT NOT NULL,
    contract_content_ref TEXT NOT NULL,
    seed BIGINT NOT NULL,
    job_id TEXT NOT NULL
);
