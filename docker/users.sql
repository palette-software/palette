--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.9
-- Dumped by pg_dump version 9.3.5
-- Started on 2016-07-05 08:42:44 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- TOC entry 2249 (class 0 OID 19229)
-- Dependencies: 286
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: palette
--

COPY users (userid, envid, active, name, friendly_name, email, email_level, hashed_password, salt, roleid, system_user_id, login_at, licensing_role_id, user_admin_level, system_admin_level, publisher, system_created_at, "timestamp", modification_time, phone) FROM stdin;
0	1	f	Palette	Palette Server Admin	\N	1	ecad6125f58c7518530d30242c133d53295d03ad		3	0	\N	\N	\N	\N	\N	\N	2016-07-04 12:56:40.875361	2016-07-04 12:56:40.864317	\N
\.


--
-- TOC entry 2254 (class 0 OID 0)
-- Dependencies: 285
-- Name: users_userid_seq; Type: SEQUENCE SET; Schema: public; Owner: palette
--

SELECT pg_catalog.setval('users_userid_seq', 120, true);


-- Completed on 2016-07-05 08:43:14 CEST

--
-- PostgreSQL database dump complete
--

