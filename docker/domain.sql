--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.9
-- Dumped by pg_dump version 9.3.5
-- Started on 2016-07-05 08:23:24 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- TOC entry 2245 (class 0 OID 19166)
-- Dependencies: 279
-- Data for Name: domain; Type: TABLE DATA; Schema: public; Owner: palette
--

COPY domain (domainid, name, license_key, systemid, expiration_time, contact_time, contact_failures, trial, creation_time, modification_time) FROM stdin;
338	default.local	0fe9a75f-8e81-459c-90b0-4259a28af7d7	f48585e6-50c8-11e5-9f8b-1279f4c4f443	2120-08-30 07:30:20.443791	2016-07-05 06:23:02.750721	0	f	2015-09-01 16:46:13.745788	2015-09-01 16:46:13.745788
\.


--
-- TOC entry 2250 (class 0 OID 0)
-- Dependencies: 278
-- Name: domain_domainid_seq; Type: SEQUENCE SET; Schema: public; Owner: palette
--

SELECT pg_catalog.setval('domain_domainid_seq', 1, false);


-- Completed on 2016-07-05 08:23:39 CEST

--
-- PostgreSQL database dump complete
--

