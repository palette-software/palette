--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.9
-- Dumped by pg_dump version 9.3.5
-- Started on 2016-07-05 08:44:29 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- TOC entry 2244 (class 0 OID 19101)
-- Dependencies: 273
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: palette
--

COPY roles (roleid, name) FROM stdin;
0	None
1	Read-Only Admin
2	Manager Admin
3	Super Admin
\.


--
-- TOC entry 2249 (class 0 OID 0)
-- Dependencies: 272
-- Name: roles_roleid_seq; Type: SEQUENCE SET; Schema: public; Owner: palette
--

SELECT pg_catalog.setval('roles_roleid_seq', 1, false);


-- Completed on 2016-07-05 08:44:44 CEST

--
-- PostgreSQL database dump complete
--

