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



--
-- Data for Name: contract_contents; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: publications; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: canonical_results; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: contract_activations; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: evaluator_calls; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: seed_results; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Name: activation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.activation_id_seq', 1, false);


--
-- Name: completion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.completion_id_seq', 1, false);


--
-- Name: evaluator_calls_call_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.evaluator_calls_call_id_seq', 1, false);


--
-- Name: job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.job_id_seq', 1, false);


--
-- Name: publication_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.publication_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

