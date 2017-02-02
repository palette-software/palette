--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.9
-- Dumped by pg_dump version 9.3.5
-- Started on 2016-07-05 08:21:40 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- TOC entry 2246 (class 0 OID 19193)
-- Dependencies: 283
-- Data for Name: environment; Type: TABLE DATA; Schema: public; Owner: palette
--

COPY environment (envid, domainid, name, creation_time, modification_time) FROM stdin;
1	338	Staging Single Node	2015-09-01 16:46:13.749812	2015-09-01 16:46:13.749812
\.


--
-- TOC entry 2251 (class 0 OID 0)
-- Dependencies: 282
-- Name: environment_envid_seq; Type: SEQUENCE SET; Schema: public; Owner: palette
--

SELECT pg_catalog.setval('environment_envid_seq', 1, false);


-- Completed on 2016-07-05 08:21:56 CEST

--
-- PostgreSQL database dump complete
--

