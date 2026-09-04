--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg120+2)
-- Dumped by pg_dump version 16.4 (Debian 16.4-1.pgdg120+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: checkpoint_contents; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.checkpoint_contents (checkpoint_content_ref, document) VALUES ('checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', '{"format": "tabular-policy-v1", "run_id": "atlas-training", "actions": {"s0": 1, "s1": 0, "s2": 2, "s3": 1}, "checkpoint_name": "candidate"}');
INSERT INTO public.checkpoint_contents (checkpoint_content_ref, document) VALUES ('checkpoint:6845da93ccd6f3cea6f16ca00919b75b6d58d821777598f226e7f4f5d3672a75', '{"format": "tabular-policy-v1", "run_id": "atlas-training", "actions": {"s0": 0, "s1": 2, "s2": 1, "s3": 1}, "checkpoint_name": "candidate"}');


--
-- Data for Name: contract_contents; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.contract_contents (contract_content_ref, document) VALUES ('contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', '{"seeds": [{"seed": 17, "cases": [{"reward": 3, "observation": "s0", "expected_action": 1}, {"reward": 2, "observation": "s1", "expected_action": 0}]}, {"seed": 29, "cases": [{"reward": 5, "observation": "s2", "expected_action": 2}, {"reward": 1, "observation": "s3", "expected_action": 0}]}], "format": "evaluation-contract-v1", "suite_name": "policy-quality", "aggregation": "sum", "dataset_revision": "dataset-2026-05", "evaluator_revision": "policy-match-v1"}');
INSERT INTO public.contract_contents (contract_content_ref, document) VALUES ('contract:0e329394ec3d24c459cc1f11ce3e25e4363b943a68bee2db1738607dba638d96', '{"seeds": [{"seed": 17, "cases": [{"reward": 4, "observation": "s0", "expected_action": 0}, {"reward": 3, "observation": "s1", "expected_action": 2}]}, {"seed": 41, "cases": [{"reward": 6, "observation": "s2", "expected_action": 1}, {"reward": 2, "observation": "s3", "expected_action": 1}]}], "format": "evaluation-contract-v1", "suite_name": "policy-quality", "aggregation": "sum", "dataset_revision": "dataset-2026-06", "evaluator_revision": "policy-match-v1"}');


--
-- Data for Name: publications; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.publications (publication_id, publication_seq, candidate_id, checkpoint_content_ref, checkpoint_label) VALUES ('pub-1', 1, 'atlas', 'checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'atlas-training:candidate');
INSERT INTO public.publications (publication_id, publication_seq, candidate_id, checkpoint_content_ref, checkpoint_label) VALUES ('pub-2', 2, 'atlas', 'checkpoint:6845da93ccd6f3cea6f16ca00919b75b6d58d821777598f226e7f4f5d3672a75', 'atlas-training:candidate');


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.jobs (job_id, job_seq, candidate_id, publication_id, checkpoint_content_ref, contract_content_ref, checkpoint_label, contract_label, status, reused, resolved_checkpoint_content_ref, resolved_contract_content_ref, completed_seq) VALUES ('job-1', 1, 'atlas', 'pub-1', 'checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 'atlas-training:candidate', 'policy-quality', 'complete', false, 'checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 2);
INSERT INTO public.jobs (job_id, job_seq, candidate_id, publication_id, checkpoint_content_ref, contract_content_ref, checkpoint_label, contract_label, status, reused, resolved_checkpoint_content_ref, resolved_contract_content_ref, completed_seq) VALUES ('job-2', 2, 'atlas', 'pub-1', 'checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 'atlas-training:candidate', 'policy-quality', 'queued', false, NULL, NULL, NULL);


--
-- Data for Name: canonical_results; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.canonical_results (checkpoint_content_ref, contract_content_ref, score, seed_count, completed_by_job_id, completed_seq) VALUES ('checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 10, 2, 'job-1', 1);


--
-- Data for Name: contract_activations; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.contract_activations (activation_id, activation_seq, contract_content_ref, contract_label) VALUES ('act-1', 1, 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 'policy-quality');
INSERT INTO public.contract_activations (activation_id, activation_seq, contract_content_ref, contract_label) VALUES ('act-2', 2, 'contract:0e329394ec3d24c459cc1f11ce3e25e4363b943a68bee2db1738607dba638d96', 'policy-quality');


--
-- Data for Name: evaluator_calls; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.evaluator_calls (call_id, checkpoint_content_ref, contract_content_ref, seed, job_id) VALUES (1, 'checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 17, 'job-1');
INSERT INTO public.evaluator_calls (call_id, checkpoint_content_ref, contract_content_ref, seed, job_id) VALUES (2, 'checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 29, 'job-1');


--
-- Data for Name: seed_results; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.seed_results (checkpoint_content_ref, contract_content_ref, seed, score, source_job_id) VALUES ('checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 17, 5, 'job-1');
INSERT INTO public.seed_results (checkpoint_content_ref, contract_content_ref, seed, score, source_job_id) VALUES ('checkpoint:13acdeabe2add302cc0a5a635ccbca027ddbea89bc026ce8db449ebdd335e4d5', 'contract:e20d445739463dca32c108629fed77800804eb38545d792fc1a54668a2c5bdda', 29, 5, 'job-1');


--
-- Name: activation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.activation_id_seq', 2, true);


--
-- Name: completion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.completion_id_seq', 2, true);


--
-- Name: evaluator_calls_call_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluator_calls_call_id_seq', 2, true);


--
-- Name: job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.job_id_seq', 2, true);


--
-- Name: publication_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.publication_id_seq', 2, true);


--
-- PostgreSQL database dump complete
--

