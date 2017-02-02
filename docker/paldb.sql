--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.9
-- Dumped by pg_dump version 9.3.5
-- Started on 2016-07-04 08:37:22 CEST

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 306 (class 1259 OID 19443)
-- Name: agent; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE agent (
    agentid bigint NOT NULL,
    conn_id bigint,
    envid bigint,
    uuid character varying,
    displayname character varying,
    display_order integer,
    enabled boolean NOT NULL,
    hostname character varying,
    fqdn character varying,
    agent_type character varying,
    version character varying,
    ip_address character varying,
    peername character varying,
    listen_port integer,
    username character varying,
    password character varying,
    os_version character varying,
    installed_memory bigint,
    processor_type character varying,
    processor_count integer,
    bitness integer,
    install_dir character varying NOT NULL,
    data_dir character varying,
    tableau_install_dir character varying,
    tableau_data_dir character varying,
    tableau_data_size bigint,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now(),
    last_connection_time timestamp without time zone DEFAULT now(),
    last_disconnect_time timestamp without time zone
);


ALTER TABLE public.agent OWNER TO palette;

--
-- TOC entry 305 (class 1259 OID 19441)
-- Name: agent_agentid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE agent_agentid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.agent_agentid_seq OWNER TO palette;

--
-- TOC entry 2521 (class 0 OID 0)
-- Dependencies: 305
-- Name: agent_agentid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE agent_agentid_seq OWNED BY agent.agentid;


--
-- TOC entry 320 (class 1259 OID 19580)
-- Name: agent_volumes; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE agent_volumes (
    volid integer NOT NULL,
    agentid bigint NOT NULL,
    name character varying,
    path character varying,
    vol_type character varying,
    label character varying,
    drive_format character varying,
    size bigint,
    available_space bigint,
    watermark_notified_color character varying(1),
    system boolean,
    archive boolean,
    archive_limit bigint,
    active boolean
);


ALTER TABLE public.agent_volumes OWNER TO palette;

--
-- TOC entry 319 (class 1259 OID 19578)
-- Name: agent_volumes_volid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE agent_volumes_volid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.agent_volumes_volid_seq OWNER TO palette;

--
-- TOC entry 2522 (class 0 OID 0)
-- Dependencies: 319
-- Name: agent_volumes_volid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE agent_volumes_volid_seq OWNED BY agent_volumes.volid;


--
-- TOC entry 292 (class 1259 OID 19313)
-- Name: cloud; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE cloud (
    cloudid bigint NOT NULL,
    envid bigint,
    cloud_type character varying,
    name character varying,
    bucket character varying NOT NULL,
    access_key character varying NOT NULL,
    secret character varying NOT NULL,
    region character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.cloud OWNER TO palette;

--
-- TOC entry 291 (class 1259 OID 19311)
-- Name: cloud_cloudid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE cloud_cloudid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cloud_cloudid_seq OWNER TO palette;

--
-- TOC entry 2523 (class 0 OID 0)
-- Dependencies: 291
-- Name: cloud_cloudid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE cloud_cloudid_seq OWNED BY cloud.cloudid;


--
-- TOC entry 294 (class 1259 OID 19334)
-- Name: credentials; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE credentials (
    credid bigint NOT NULL,
    envid integer NOT NULL,
    key character varying NOT NULL,
    "user" character varying,
    embedded character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.credentials OWNER TO palette;

--
-- TOC entry 293 (class 1259 OID 19332)
-- Name: credentials_credid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE credentials_credid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.credentials_credid_seq OWNER TO palette;

--
-- TOC entry 2524 (class 0 OID 0)
-- Dependencies: 293
-- Name: credentials_credid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE credentials_credid_seq OWNED BY credentials.credid;


--
-- TOC entry 336 (class 1259 OID 113436)
-- Name: cron; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE cron (
    cronid bigint NOT NULL,
    name character varying NOT NULL,
    next_run_time timestamp without time zone,
    minute character varying NOT NULL,
    hour character varying NOT NULL,
    day_of_month character varying NOT NULL,
    month character varying NOT NULL,
    day_of_week character varying NOT NULL,
    enabled boolean NOT NULL,
    priority integer
);


ALTER TABLE public.cron OWNER TO palette;

--
-- TOC entry 335 (class 1259 OID 113434)
-- Name: cron_cronid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE cron_cronid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cron_cronid_seq OWNER TO palette;

--
-- TOC entry 2525 (class 0 OID 0)
-- Dependencies: 335
-- Name: cron_cronid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE cron_cronid_seq OWNED BY cron.cronid;


--
-- TOC entry 308 (class 1259 OID 19463)
-- Name: data_connections; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE data_connections (
    dcid bigint NOT NULL,
    envid integer NOT NULL,
    id integer NOT NULL,
    server character varying,
    dbclass character varying,
    port integer,
    username character varying,
    password boolean,
    name character varying,
    dbname character varying,
    tablename character varying,
    owner_type character varying,
    owner_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    caption character varying,
    site_id integer,
    keychain character varying
);


ALTER TABLE public.data_connections OWNER TO palette;

--
-- TOC entry 307 (class 1259 OID 19461)
-- Name: data_connections_dcid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE data_connections_dcid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_connections_dcid_seq OWNER TO palette;

--
-- TOC entry 2526 (class 0 OID 0)
-- Dependencies: 307
-- Name: data_connections_dcid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE data_connections_dcid_seq OWNED BY data_connections.dcid;


--
-- TOC entry 281 (class 1259 OID 19180)
-- Name: data_source_types; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE data_source_types (
    datastid bigint NOT NULL,
    data_source character varying,
    standard_port integer,
    standard_host character varying,
    driver_version character varying,
    driver_install_location character varying,
    dbclass character varying
);


ALTER TABLE public.data_source_types OWNER TO palette;

--
-- TOC entry 280 (class 1259 OID 19178)
-- Name: data_source_types_datastid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE data_source_types_datastid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_source_types_datastid_seq OWNER TO palette;

--
-- TOC entry 2527 (class 0 OID 0)
-- Dependencies: 280
-- Name: data_source_types_datastid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE data_source_types_datastid_seq OWNED BY data_source_types.datastid;


--
-- TOC entry 340 (class 1259 OID 113474)
-- Name: datasource_extracts; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE datasource_extracts (
    sid bigint NOT NULL,
    extractid bigint,
    parentid bigint,
    fileid integer,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.datasource_extracts OWNER TO palette;

--
-- TOC entry 339 (class 1259 OID 113472)
-- Name: datasource_extracts_sid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE datasource_extracts_sid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.datasource_extracts_sid_seq OWNER TO palette;

--
-- TOC entry 2528 (class 0 OID 0)
-- Dependencies: 339
-- Name: datasource_extracts_sid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE datasource_extracts_sid_seq OWNED BY datasource_extracts.sid;


--
-- TOC entry 334 (class 1259 OID 113139)
-- Name: datasource_updates; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE datasource_updates (
    dsuid bigint NOT NULL,
    dsid bigint,
    revision character varying NOT NULL,
    fileid_tds integer,
    fileid_tdsx integer,
    "timestamp" timestamp without time zone NOT NULL,
    system_user_id integer,
    url character varying,
    note character varying,
    tds text
);


ALTER TABLE public.datasource_updates OWNER TO palette;

--
-- TOC entry 333 (class 1259 OID 113137)
-- Name: datasource_updates_dsuid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE datasource_updates_dsuid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.datasource_updates_dsuid_seq OWNER TO palette;

--
-- TOC entry 2529 (class 0 OID 0)
-- Dependencies: 333
-- Name: datasource_updates_dsuid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE datasource_updates_dsuid_seq OWNED BY datasource_updates.dsuid;


--
-- TOC entry 332 (class 1259 OID 113121)
-- Name: datasources; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE datasources (
    dsid bigint NOT NULL,
    envid integer NOT NULL,
    system_user_id integer,
    id integer NOT NULL,
    name character varying,
    repository_url character varying,
    owner_id integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    project_id integer,
    size bigint,
    lock_version integer,
    state character varying,
    db_class character varying,
    db_name character varying,
    table_name character varying,
    site_id integer,
    repository_data_id bigint,
    repository_extract_data_id bigint,
    embedded character varying,
    incremental_extracts boolean,
    refreshable_extracts boolean,
    data_engine_extracts boolean,
    extracts_refreshed_at timestamp without time zone,
    first_published_at timestamp without time zone,
    connectable boolean,
    is_hierarchical boolean,
    extracts_incremented_at timestamp without time zone,
    luid character varying,
    asset_key_id integer,
    document_version character varying,
    description character varying
);


ALTER TABLE public.datasources OWNER TO palette;

--
-- TOC entry 331 (class 1259 OID 113119)
-- Name: datasources_dsid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE datasources_dsid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.datasources_dsid_seq OWNER TO palette;

--
-- TOC entry 2530 (class 0 OID 0)
-- Dependencies: 331
-- Name: datasources_dsid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE datasources_dsid_seq OWNED BY datasources.dsid;


--
-- TOC entry 279 (class 1259 OID 19166)
-- Name: domain; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE domain (
    domainid bigint NOT NULL,
    name character varying NOT NULL,
    license_key character varying,
    systemid character varying,
    expiration_time timestamp without time zone,
    contact_time timestamp without time zone,
    contact_failures integer,
    trial boolean,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.domain OWNER TO palette;

--
-- TOC entry 278 (class 1259 OID 19164)
-- Name: domain_domainid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE domain_domainid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.domain_domainid_seq OWNER TO palette;

--
-- TOC entry 2531 (class 0 OID 0)
-- Dependencies: 278
-- Name: domain_domainid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE domain_domainid_seq OWNED BY domain.domainid;


--
-- TOC entry 302 (class 1259 OID 19411)
-- Name: email_sent; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE email_sent (
    emailid bigint NOT NULL,
    envid bigint,
    eventid bigint,
    creation_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.email_sent OWNER TO palette;

--
-- TOC entry 301 (class 1259 OID 19409)
-- Name: email_sent_emailid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE email_sent_emailid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.email_sent_emailid_seq OWNER TO palette;

--
-- TOC entry 2532 (class 0 OID 0)
-- Dependencies: 301
-- Name: email_sent_emailid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE email_sent_emailid_seq OWNED BY email_sent.emailid;


--
-- TOC entry 283 (class 1259 OID 19193)
-- Name: environment; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE environment (
    envid bigint NOT NULL,
    domainid bigint,
    name character varying NOT NULL,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.environment OWNER TO palette;

--
-- TOC entry 282 (class 1259 OID 19191)
-- Name: environment_envid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE environment_envid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.environment_envid_seq OWNER TO palette;

--
-- TOC entry 2533 (class 0 OID 0)
-- Dependencies: 282
-- Name: environment_envid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE environment_envid_seq OWNED BY environment.envid;


--
-- TOC entry 330 (class 1259 OID 104426)
-- Name: event_control; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE event_control (
    eventid bigint NOT NULL,
    key character varying NOT NULL,
    level character varying(1),
    send_email boolean,
    subject character varying,
    event_description character varying,
    email_subject character varying,
    email_message character varying,
    icon character varying,
    color character varying,
    event_type character varying,
    event_type_label character varying,
    event_label character varying,
    event_label_desc character varying,
    admin_visibility boolean,
    publisher_visibility boolean,
    custom boolean DEFAULT false
);


ALTER TABLE public.event_control OWNER TO palette;

--
-- TOC entry 329 (class 1259 OID 104424)
-- Name: event_control_eventid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE event_control_eventid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.event_control_eventid_seq OWNER TO palette;

--
-- TOC entry 2534 (class 0 OID 0)
-- Dependencies: 329
-- Name: event_control_eventid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE event_control_eventid_seq OWNED BY event_control.eventid;


--
-- TOC entry 298 (class 1259 OID 19372)
-- Name: events; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE events (
    eventid bigint NOT NULL,
    envid bigint,
    complete boolean,
    key character varying NOT NULL,
    title character varying,
    summary character varying,
    description character varying,
    level character varying(1),
    icon character varying,
    color character varying,
    event_type character varying,
    userid integer,
    site_id integer,
    project_id integer,
    creation_time timestamp without time zone DEFAULT now(),
    "timestamp" timestamp without time zone DEFAULT now()
);


ALTER TABLE public.events OWNER TO palette;

--
-- TOC entry 297 (class 1259 OID 19370)
-- Name: events_eventid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE events_eventid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.events_eventid_seq OWNER TO palette;

--
-- TOC entry 2535 (class 0 OID 0)
-- Dependencies: 297
-- Name: events_eventid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE events_eventid_seq OWNED BY events.eventid;


--
-- TOC entry 290 (class 1259 OID 19295)
-- Name: extracts; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE extracts (
    extractid bigint NOT NULL,
    envid bigint NOT NULL,
    id bigint NOT NULL,
    args character varying,
    notes character varying,
    finish_code integer NOT NULL,
    priority integer,
    updated_at timestamp without time zone,
    created_at timestamp without time zone,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    title character varying,
    created_on_worker character varying,
    processed_on_worker character varying,
    link character varying,
    lock_version character varying,
    backgrounder_id character varying,
    subtitle character varying,
    language character varying,
    locale character varying,
    site_id integer,
    project_id integer,
    system_user_id integer,
    job_name character varying,
    progress integer,
    job_type character varying,
    notification_state integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.extracts OWNER TO palette;

--
-- TOC entry 289 (class 1259 OID 19293)
-- Name: extracts_extractid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE extracts_extractid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.extracts_extractid_seq OWNER TO palette;

--
-- TOC entry 2536 (class 0 OID 0)
-- Dependencies: 289
-- Name: extracts_extractid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE extracts_extractid_seq OWNED BY extracts.extractid;


--
-- TOC entry 300 (class 1259 OID 19393)
-- Name: files; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE files (
    fileid integer NOT NULL,
    envid bigint,
    name character varying,
    file_type character varying,
    username character varying,
    storage_type character varying,
    storageid bigint,
    size bigint,
    auto boolean,
    encrypted boolean,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.files OWNER TO palette;

--
-- TOC entry 299 (class 1259 OID 19391)
-- Name: files_fileid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE files_fileid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.files_fileid_seq OWNER TO palette;

--
-- TOC entry 2537 (class 0 OID 0)
-- Dependencies: 299
-- Name: files_fileid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE files_fileid_seq OWNED BY files.fileid;


--
-- TOC entry 326 (class 1259 OID 19633)
-- Name: firewall; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE firewall (
    firewallid bigint NOT NULL,
    agentid bigint NOT NULL,
    name character varying,
    port integer NOT NULL,
    color character varying,
    status character varying
);


ALTER TABLE public.firewall OWNER TO palette;

--
-- TOC entry 325 (class 1259 OID 19631)
-- Name: firewall_firewallid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE firewall_firewallid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.firewall_firewallid_seq OWNER TO palette;

--
-- TOC entry 2538 (class 0 OID 0)
-- Dependencies: 325
-- Name: firewall_firewallid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE firewall_firewallid_seq OWNED BY firewall.firewallid;


--
-- TOC entry 271 (class 1259 OID 19086)
-- Name: http_control; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE http_control (
    hcid bigint NOT NULL,
    status bigint NOT NULL,
    level integer NOT NULL,
    excludes character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.http_control OWNER TO palette;

--
-- TOC entry 270 (class 1259 OID 19084)
-- Name: http_control_hcid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE http_control_hcid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.http_control_hcid_seq OWNER TO palette;

--
-- TOC entry 2539 (class 0 OID 0)
-- Dependencies: 270
-- Name: http_control_hcid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE http_control_hcid_seq OWNED BY http_control.hcid;


--
-- TOC entry 312 (class 1259 OID 19501)
-- Name: http_requests; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE http_requests (
    reqid bigint NOT NULL,
    envid bigint NOT NULL,
    system_user_id character varying,
    id bigint NOT NULL,
    controller character varying,
    action character varying,
    http_referer character varying,
    http_user_agent character varying,
    http_request_uri character varying,
    remote_ip character varying,
    created_at timestamp without time zone,
    session_id character varying,
    completed_at timestamp without time zone,
    port integer,
    user_id integer,
    worker character varying,
    status integer,
    user_cookie character varying,
    user_ip character varying,
    vizql_session character varying,
    site_id integer,
    currentsheet character varying
);


ALTER TABLE public.http_requests OWNER TO palette;

--
-- TOC entry 311 (class 1259 OID 19499)
-- Name: http_requests_reqid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE http_requests_reqid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.http_requests_reqid_seq OWNER TO palette;

--
-- TOC entry 2540 (class 0 OID 0)
-- Dependencies: 311
-- Name: http_requests_reqid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE http_requests_reqid_seq OWNED BY http_requests.reqid;


--
-- TOC entry 316 (class 1259 OID 19542)
-- Name: license; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE license (
    licenseid bigint NOT NULL,
    agentid bigint NOT NULL,
    interactors integer,
    viewers integer,
    cores integer,
    core_licenses integer,
    license_type character varying,
    notified boolean NOT NULL,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.license OWNER TO palette;

--
-- TOC entry 315 (class 1259 OID 19540)
-- Name: license_licenseid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE license_licenseid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.license_licenseid_seq OWNER TO palette;

--
-- TOC entry 2541 (class 0 OID 0)
-- Dependencies: 315
-- Name: license_licenseid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE license_licenseid_seq OWNED BY license.licenseid;


--
-- TOC entry 324 (class 1259 OID 19619)
-- Name: metrics; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE metrics (
    metricid bigint NOT NULL,
    agentid bigint NOT NULL,
    cpu double precision,
    creation_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.metrics OWNER TO palette;

--
-- TOC entry 323 (class 1259 OID 19617)
-- Name: metrics_metricid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE metrics_metricid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_metricid_seq OWNER TO palette;

--
-- TOC entry 2542 (class 0 OID 0)
-- Dependencies: 323
-- Name: metrics_metricid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE metrics_metricid_seq OWNED BY metrics.metricid;


--
-- TOC entry 314 (class 1259 OID 19519)
-- Name: notifications; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE notifications (
    notificationid bigint NOT NULL,
    envid bigint,
    name character varying,
    agentid bigint,
    color character varying,
    notified_color character varying,
    description character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.notifications OWNER TO palette;

--
-- TOC entry 313 (class 1259 OID 19517)
-- Name: notifications_notificationid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE notifications_notificationid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.notifications_notificationid_seq OWNER TO palette;

--
-- TOC entry 2543 (class 0 OID 0)
-- Dependencies: 313
-- Name: notifications_notificationid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE notifications_notificationid_seq OWNED BY notifications.notificationid;


--
-- TOC entry 328 (class 1259 OID 19649)
-- Name: ports; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE ports (
    portid bigint NOT NULL,
    envid bigint,
    dest_host character varying NOT NULL,
    dest_port integer NOT NULL,
    service_name character varying NOT NULL,
    agentid bigint NOT NULL,
    ip_address character varying,
    connect_time double precision,
    max_time integer NOT NULL,
    color character varying,
    notified_color character varying,
    active boolean,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.ports OWNER TO palette;

--
-- TOC entry 327 (class 1259 OID 19647)
-- Name: ports_portid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE ports_portid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ports_portid_seq OWNER TO palette;

--
-- TOC entry 2544 (class 0 OID 0)
-- Dependencies: 327
-- Name: ports_portid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE ports_portid_seq OWNED BY ports.portid;


--
-- TOC entry 296 (class 1259 OID 19354)
-- Name: projects; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE projects (
    projectid bigint NOT NULL,
    envid integer NOT NULL,
    id integer NOT NULL,
    name character varying NOT NULL,
    owner_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    state character varying(32),
    description character varying,
    site_id integer NOT NULL,
    special integer
);


ALTER TABLE public.projects OWNER TO palette;

--
-- TOC entry 295 (class 1259 OID 19352)
-- Name: projects_projectid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE projects_projectid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_projectid_seq OWNER TO palette;

--
-- TOC entry 2545 (class 0 OID 0)
-- Dependencies: 295
-- Name: projects_projectid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE projects_projectid_seq OWNED BY projects.projectid;


--
-- TOC entry 273 (class 1259 OID 19101)
-- Name: roles; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE roles (
    roleid bigint NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.roles OWNER TO palette;

--
-- TOC entry 272 (class 1259 OID 19099)
-- Name: roles_roleid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE roles_roleid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_roleid_seq OWNER TO palette;

--
-- TOC entry 2546 (class 0 OID 0)
-- Dependencies: 272
-- Name: roles_roleid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE roles_roleid_seq OWNED BY roles.roleid;


--
-- TOC entry 310 (class 1259 OID 19481)
-- Name: sites; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE sites (
    siteid bigint NOT NULL,
    envid integer NOT NULL,
    id integer NOT NULL,
    name character varying NOT NULL,
    url_namespace character varying,
    status character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    user_quota integer,
    content_admin_mode integer,
    storage_quota bigint,
    metrics_level smallint,
    status_reason character varying,
    subscriptions_enabled boolean NOT NULL,
    custom_subscription_footer character varying,
    custom_subscription_email character varying,
    luid character varying,
    query_limit integer
);


ALTER TABLE public.sites OWNER TO palette;

--
-- TOC entry 309 (class 1259 OID 19479)
-- Name: sites_siteid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE sites_siteid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.sites_siteid_seq OWNER TO palette;

--
-- TOC entry 2547 (class 0 OID 0)
-- Dependencies: 309
-- Name: sites_siteid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE sites_siteid_seq OWNED BY sites.siteid;


--
-- TOC entry 275 (class 1259 OID 19140)
-- Name: state_control; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE state_control (
    stateid bigint NOT NULL,
    state character varying,
    text character varying,
    allowable_actions character varying,
    icon character varying,
    color character varying
);


ALTER TABLE public.state_control OWNER TO palette;

--
-- TOC entry 274 (class 1259 OID 19138)
-- Name: state_control_stateid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE state_control_stateid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.state_control_stateid_seq OWNER TO palette;

--
-- TOC entry 2548 (class 0 OID 0)
-- Dependencies: 274
-- Name: state_control_stateid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE state_control_stateid_seq OWNED BY state_control.stateid;


--
-- TOC entry 284 (class 1259 OID 19210)
-- Name: system; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE system (
    envid bigint NOT NULL,
    key character varying NOT NULL,
    value character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.system OWNER TO palette;

--
-- TOC entry 318 (class 1259 OID 19562)
-- Name: tableau_processes; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE tableau_processes (
    tid bigint NOT NULL,
    name character varying NOT NULL,
    agentid bigint NOT NULL,
    pid integer,
    status character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.tableau_processes OWNER TO palette;

--
-- TOC entry 317 (class 1259 OID 19560)
-- Name: tableau_processes_tid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE tableau_processes_tid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tableau_processes_tid_seq OWNER TO palette;

--
-- TOC entry 2549 (class 0 OID 0)
-- Dependencies: 317
-- Name: tableau_processes_tid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE tableau_processes_tid_seq OWNED BY tableau_processes.tid;


--
-- TOC entry 286 (class 1259 OID 19229)
-- Name: users; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE users (
    userid bigint NOT NULL,
    envid bigint NOT NULL,
    active boolean,
    name character varying NOT NULL,
    friendly_name character varying,
    email character varying,
    email_level integer,
    hashed_password character varying,
    salt character varying,
    roleid bigint,
    system_user_id integer,
    login_at timestamp without time zone,
    licensing_role_id integer,
    user_admin_level integer,
    system_admin_level integer,
    publisher boolean,
    system_created_at timestamp without time zone,
    "timestamp" timestamp without time zone,
    modification_time timestamp without time zone DEFAULT now(),
    phone character varying
);


ALTER TABLE public.users OWNER TO palette;

--
-- TOC entry 285 (class 1259 OID 19227)
-- Name: users_userid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE users_userid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_userid_seq OWNER TO palette;

--
-- TOC entry 2550 (class 0 OID 0)
-- Dependencies: 285
-- Name: users_userid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE users_userid_seq OWNED BY users.userid;


--
-- TOC entry 338 (class 1259 OID 113449)
-- Name: workbook_extracts; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE workbook_extracts (
    sid bigint NOT NULL,
    extractid bigint,
    parentid bigint,
    fileid integer,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.workbook_extracts OWNER TO palette;

--
-- TOC entry 337 (class 1259 OID 113447)
-- Name: workbook_extracts_sid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE workbook_extracts_sid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workbook_extracts_sid_seq OWNER TO palette;

--
-- TOC entry 2551 (class 0 OID 0)
-- Dependencies: 337
-- Name: workbook_extracts_sid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE workbook_extracts_sid_seq OWNED BY workbook_extracts.sid;


--
-- TOC entry 322 (class 1259 OID 19596)
-- Name: workbook_updates; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE workbook_updates (
    wuid bigint NOT NULL,
    workbookid bigint,
    revision character varying NOT NULL,
    fileid integer,
    "timestamp" timestamp without time zone NOT NULL,
    system_user_id integer,
    url character varying,
    note character varying,
    fileid_twbx integer,
    twb text
);


ALTER TABLE public.workbook_updates OWNER TO palette;

--
-- TOC entry 321 (class 1259 OID 19594)
-- Name: workbook_updates_wuid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE workbook_updates_wuid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workbook_updates_wuid_seq OWNER TO palette;

--
-- TOC entry 2552 (class 0 OID 0)
-- Dependencies: 321
-- Name: workbook_updates_wuid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE workbook_updates_wuid_seq OWNED BY workbook_updates.wuid;


--
-- TOC entry 304 (class 1259 OID 19425)
-- Name: workbooks; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE workbooks (
    workbookid bigint NOT NULL,
    envid bigint NOT NULL,
    system_user_id integer,
    id bigint NOT NULL,
    name character varying,
    repository_url character varying,
    description character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    owner_id integer,
    project_id integer,
    view_count integer,
    size bigint,
    embedded character varying,
    thumb_user character varying,
    refreshable_extracts boolean,
    extracts_refreshed_at timestamp without time zone,
    lock_version integer,
    state character varying,
    version character varying,
    checksum character varying,
    display_tabs boolean,
    data_engine_extracts boolean,
    incrementable_extracts boolean,
    site_id integer,
    repository_data_id bigint,
    repository_extract_data_id bigint,
    first_published_at timestamp without time zone,
    primary_content_url character varying,
    share_description character varying,
    show_toolbar boolean,
    extracts_incremented_at timestamp without time zone,
    default_view_index integer,
    luid character varying,
    assert_key_id integer,
    document_version character varying
);


ALTER TABLE public.workbooks OWNER TO palette;

--
-- TOC entry 303 (class 1259 OID 19423)
-- Name: workbooks_workbookid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE workbooks_workbookid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workbooks_workbookid_seq OWNER TO palette;

--
-- TOC entry 2553 (class 0 OID 0)
-- Dependencies: 303
-- Name: workbooks_workbookid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE workbooks_workbookid_seq OWNED BY workbooks.workbookid;


--
-- TOC entry 277 (class 1259 OID 19153)
-- Name: xid; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE xid (
    xid bigint NOT NULL,
    state character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.xid OWNER TO palette;

--
-- TOC entry 276 (class 1259 OID 19151)
-- Name: xid_xid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE xid_xid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.xid_xid_seq OWNER TO palette;

--
-- TOC entry 2554 (class 0 OID 0)
-- Dependencies: 276
-- Name: xid_xid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE xid_xid_seq OWNED BY xid.xid;


--
-- TOC entry 288 (class 1259 OID 19255)
-- Name: yml; Type: TABLE; Schema: public; Owner: palette; Tablespace: 
--

CREATE TABLE yml (
    ymlid integer NOT NULL,
    envid bigint NOT NULL,
    key character varying,
    value character varying,
    creation_time timestamp without time zone DEFAULT now(),
    modification_time timestamp without time zone DEFAULT now()
);


ALTER TABLE public.yml OWNER TO palette;

--
-- TOC entry 287 (class 1259 OID 19253)
-- Name: yml_ymlid_seq; Type: SEQUENCE; Schema: public; Owner: palette
--

CREATE SEQUENCE yml_ymlid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.yml_ymlid_seq OWNER TO palette;

--
-- TOC entry 2555 (class 0 OID 0)
-- Dependencies: 287
-- Name: yml_ymlid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: palette
--

ALTER SEQUENCE yml_ymlid_seq OWNED BY yml.ymlid;


--
-- TOC entry 2207 (class 2604 OID 19446)
-- Name: agentid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY agent ALTER COLUMN agentid SET DEFAULT nextval('agent_agentid_seq'::regclass);


--
-- TOC entry 2223 (class 2604 OID 19583)
-- Name: volid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY agent_volumes ALTER COLUMN volid SET DEFAULT nextval('agent_volumes_volid_seq'::regclass);


--
-- TOC entry 2191 (class 2604 OID 19316)
-- Name: cloudid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY cloud ALTER COLUMN cloudid SET DEFAULT nextval('cloud_cloudid_seq'::regclass);


--
-- TOC entry 2194 (class 2604 OID 19337)
-- Name: credid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY credentials ALTER COLUMN credid SET DEFAULT nextval('credentials_credid_seq'::regclass);


--
-- TOC entry 2235 (class 2604 OID 113439)
-- Name: cronid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY cron ALTER COLUMN cronid SET DEFAULT nextval('cron_cronid_seq'::regclass);


--
-- TOC entry 2211 (class 2604 OID 19466)
-- Name: dcid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY data_connections ALTER COLUMN dcid SET DEFAULT nextval('data_connections_dcid_seq'::regclass);


--
-- TOC entry 2178 (class 2604 OID 19183)
-- Name: datastid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY data_source_types ALTER COLUMN datastid SET DEFAULT nextval('data_source_types_datastid_seq'::regclass);


--
-- TOC entry 2239 (class 2604 OID 113477)
-- Name: sid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_extracts ALTER COLUMN sid SET DEFAULT nextval('datasource_extracts_sid_seq'::regclass);


--
-- TOC entry 2234 (class 2604 OID 113142)
-- Name: dsuid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_updates ALTER COLUMN dsuid SET DEFAULT nextval('datasource_updates_dsuid_seq'::regclass);


--
-- TOC entry 2233 (class 2604 OID 113124)
-- Name: dsid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasources ALTER COLUMN dsid SET DEFAULT nextval('datasources_dsid_seq'::regclass);


--
-- TOC entry 2175 (class 2604 OID 19169)
-- Name: domainid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY domain ALTER COLUMN domainid SET DEFAULT nextval('domain_domainid_seq'::regclass);


--
-- TOC entry 2204 (class 2604 OID 19414)
-- Name: emailid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY email_sent ALTER COLUMN emailid SET DEFAULT nextval('email_sent_emailid_seq'::regclass);


--
-- TOC entry 2179 (class 2604 OID 19196)
-- Name: envid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY environment ALTER COLUMN envid SET DEFAULT nextval('environment_envid_seq'::regclass);


--
-- TOC entry 2231 (class 2604 OID 104429)
-- Name: eventid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY event_control ALTER COLUMN eventid SET DEFAULT nextval('event_control_eventid_seq'::regclass);


--
-- TOC entry 2198 (class 2604 OID 19375)
-- Name: eventid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY events ALTER COLUMN eventid SET DEFAULT nextval('events_eventid_seq'::regclass);


--
-- TOC entry 2189 (class 2604 OID 19298)
-- Name: extractid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY extracts ALTER COLUMN extractid SET DEFAULT nextval('extracts_extractid_seq'::regclass);


--
-- TOC entry 2201 (class 2604 OID 19396)
-- Name: fileid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY files ALTER COLUMN fileid SET DEFAULT nextval('files_fileid_seq'::regclass);


--
-- TOC entry 2227 (class 2604 OID 19636)
-- Name: firewallid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY firewall ALTER COLUMN firewallid SET DEFAULT nextval('firewall_firewallid_seq'::regclass);


--
-- TOC entry 2167 (class 2604 OID 19089)
-- Name: hcid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY http_control ALTER COLUMN hcid SET DEFAULT nextval('http_control_hcid_seq'::regclass);


--
-- TOC entry 2213 (class 2604 OID 19504)
-- Name: reqid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY http_requests ALTER COLUMN reqid SET DEFAULT nextval('http_requests_reqid_seq'::regclass);


--
-- TOC entry 2217 (class 2604 OID 19545)
-- Name: licenseid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY license ALTER COLUMN licenseid SET DEFAULT nextval('license_licenseid_seq'::regclass);


--
-- TOC entry 2225 (class 2604 OID 19622)
-- Name: metricid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY metrics ALTER COLUMN metricid SET DEFAULT nextval('metrics_metricid_seq'::regclass);


--
-- TOC entry 2214 (class 2604 OID 19522)
-- Name: notificationid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY notifications ALTER COLUMN notificationid SET DEFAULT nextval('notifications_notificationid_seq'::regclass);


--
-- TOC entry 2228 (class 2604 OID 19652)
-- Name: portid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY ports ALTER COLUMN portid SET DEFAULT nextval('ports_portid_seq'::regclass);


--
-- TOC entry 2197 (class 2604 OID 19357)
-- Name: projectid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY projects ALTER COLUMN projectid SET DEFAULT nextval('projects_projectid_seq'::regclass);


--
-- TOC entry 2170 (class 2604 OID 19104)
-- Name: roleid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY roles ALTER COLUMN roleid SET DEFAULT nextval('roles_roleid_seq'::regclass);


--
-- TOC entry 2212 (class 2604 OID 19484)
-- Name: siteid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY sites ALTER COLUMN siteid SET DEFAULT nextval('sites_siteid_seq'::regclass);


--
-- TOC entry 2171 (class 2604 OID 19143)
-- Name: stateid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY state_control ALTER COLUMN stateid SET DEFAULT nextval('state_control_stateid_seq'::regclass);


--
-- TOC entry 2220 (class 2604 OID 19565)
-- Name: tid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY tableau_processes ALTER COLUMN tid SET DEFAULT nextval('tableau_processes_tid_seq'::regclass);


--
-- TOC entry 2184 (class 2604 OID 19232)
-- Name: userid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY users ALTER COLUMN userid SET DEFAULT nextval('users_userid_seq'::regclass);


--
-- TOC entry 2236 (class 2604 OID 113452)
-- Name: sid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_extracts ALTER COLUMN sid SET DEFAULT nextval('workbook_extracts_sid_seq'::regclass);


--
-- TOC entry 2224 (class 2604 OID 19599)
-- Name: wuid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_updates ALTER COLUMN wuid SET DEFAULT nextval('workbook_updates_wuid_seq'::regclass);


--
-- TOC entry 2206 (class 2604 OID 19428)
-- Name: workbookid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbooks ALTER COLUMN workbookid SET DEFAULT nextval('workbooks_workbookid_seq'::regclass);


--
-- TOC entry 2172 (class 2604 OID 19156)
-- Name: xid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY xid ALTER COLUMN xid SET DEFAULT nextval('xid_xid_seq'::regclass);


--
-- TOC entry 2186 (class 2604 OID 19258)
-- Name: ymlid; Type: DEFAULT; Schema: public; Owner: palette
--

ALTER TABLE ONLY yml ALTER COLUMN ymlid SET DEFAULT nextval('yml_ymlid_seq'::regclass);


--
-- TOC entry 2313 (class 2606 OID 19454)
-- Name: agent_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY agent
    ADD CONSTRAINT agent_pkey PRIMARY KEY (agentid);


--
-- TOC entry 2338 (class 2606 OID 19588)
-- Name: agent_volumes_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY agent_volumes
    ADD CONSTRAINT agent_volumes_pkey PRIMARY KEY (volid);


--
-- TOC entry 2287 (class 2606 OID 19325)
-- Name: cloud_envid_name_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY cloud
    ADD CONSTRAINT cloud_envid_name_key UNIQUE (envid, name);


--
-- TOC entry 2289 (class 2606 OID 19323)
-- Name: cloud_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY cloud
    ADD CONSTRAINT cloud_pkey PRIMARY KEY (cloudid);


--
-- TOC entry 2292 (class 2606 OID 19346)
-- Name: credentials_envid_key_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY credentials
    ADD CONSTRAINT credentials_envid_key_key UNIQUE (envid, key);


--
-- TOC entry 2294 (class 2606 OID 19344)
-- Name: credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY credentials
    ADD CONSTRAINT credentials_pkey PRIMARY KEY (credid);


--
-- TOC entry 2362 (class 2606 OID 113446)
-- Name: cron_name_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY cron
    ADD CONSTRAINT cron_name_key UNIQUE (name);


--
-- TOC entry 2364 (class 2606 OID 113444)
-- Name: cron_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY cron
    ADD CONSTRAINT cron_pkey PRIMARY KEY (cronid);


--
-- TOC entry 2316 (class 2606 OID 19473)
-- Name: data_connections_envid_id_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY data_connections
    ADD CONSTRAINT data_connections_envid_id_key UNIQUE (envid, id);


--
-- TOC entry 2318 (class 2606 OID 19471)
-- Name: data_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY data_connections
    ADD CONSTRAINT data_connections_pkey PRIMARY KEY (dcid);


--
-- TOC entry 2260 (class 2606 OID 19190)
-- Name: data_source_types_data_source_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY data_source_types
    ADD CONSTRAINT data_source_types_data_source_key UNIQUE (data_source);


--
-- TOC entry 2262 (class 2606 OID 19188)
-- Name: data_source_types_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY data_source_types
    ADD CONSTRAINT data_source_types_pkey PRIMARY KEY (datastid);


--
-- TOC entry 2368 (class 2606 OID 113481)
-- Name: datasource_extracts_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY datasource_extracts
    ADD CONSTRAINT datasource_extracts_pkey PRIMARY KEY (sid);


--
-- TOC entry 2358 (class 2606 OID 113149)
-- Name: datasource_updates_dsid_revision_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY datasource_updates
    ADD CONSTRAINT datasource_updates_dsid_revision_key UNIQUE (dsid, revision);


--
-- TOC entry 2360 (class 2606 OID 113147)
-- Name: datasource_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY datasource_updates
    ADD CONSTRAINT datasource_updates_pkey PRIMARY KEY (dsuid);


--
-- TOC entry 2354 (class 2606 OID 113131)
-- Name: datasources_envid_site_id_project_id_luid_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY datasources
    ADD CONSTRAINT datasources_envid_site_id_project_id_luid_key UNIQUE (envid, site_id, project_id, luid);


--
-- TOC entry 2356 (class 2606 OID 113129)
-- Name: datasources_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY datasources
    ADD CONSTRAINT datasources_pkey PRIMARY KEY (dsid);


--
-- TOC entry 2257 (class 2606 OID 19176)
-- Name: domain_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY domain
    ADD CONSTRAINT domain_pkey PRIMARY KEY (domainid);


--
-- TOC entry 2307 (class 2606 OID 19417)
-- Name: email_sent_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY email_sent
    ADD CONSTRAINT email_sent_pkey PRIMARY KEY (emailid);


--
-- TOC entry 2264 (class 2606 OID 19203)
-- Name: environment_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY environment
    ADD CONSTRAINT environment_pkey PRIMARY KEY (envid);


--
-- TOC entry 2350 (class 2606 OID 104436)
-- Name: event_control_key_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY event_control
    ADD CONSTRAINT event_control_key_key UNIQUE (key);


--
-- TOC entry 2352 (class 2606 OID 104434)
-- Name: event_control_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY event_control
    ADD CONSTRAINT event_control_pkey PRIMARY KEY (eventid);


--
-- TOC entry 2303 (class 2606 OID 19382)
-- Name: events_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY events
    ADD CONSTRAINT events_pkey PRIMARY KEY (eventid);


--
-- TOC entry 2283 (class 2606 OID 19305)
-- Name: extracts_envid_id_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY extracts
    ADD CONSTRAINT extracts_envid_id_key UNIQUE (envid, id);


--
-- TOC entry 2285 (class 2606 OID 19303)
-- Name: extracts_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY extracts
    ADD CONSTRAINT extracts_pkey PRIMARY KEY (extractid);


--
-- TOC entry 2305 (class 2606 OID 19403)
-- Name: files_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_pkey PRIMARY KEY (fileid);


--
-- TOC entry 2346 (class 2606 OID 19641)
-- Name: firewall_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY firewall
    ADD CONSTRAINT firewall_pkey PRIMARY KEY (firewallid);


--
-- TOC entry 2243 (class 2606 OID 19096)
-- Name: http_control_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY http_control
    ADD CONSTRAINT http_control_pkey PRIMARY KEY (hcid);


--
-- TOC entry 2245 (class 2606 OID 19098)
-- Name: http_control_status_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY http_control
    ADD CONSTRAINT http_control_status_key UNIQUE (status);


--
-- TOC entry 2326 (class 2606 OID 19511)
-- Name: http_requests_envid_id_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY http_requests
    ADD CONSTRAINT http_requests_envid_id_key UNIQUE (envid, id);


--
-- TOC entry 2328 (class 2606 OID 19509)
-- Name: http_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY http_requests
    ADD CONSTRAINT http_requests_pkey PRIMARY KEY (reqid);


--
-- TOC entry 2332 (class 2606 OID 19554)
-- Name: license_agentid_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY license
    ADD CONSTRAINT license_agentid_key UNIQUE (agentid);


--
-- TOC entry 2334 (class 2606 OID 19552)
-- Name: license_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY license
    ADD CONSTRAINT license_pkey PRIMARY KEY (licenseid);


--
-- TOC entry 2344 (class 2606 OID 19625)
-- Name: metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY metrics
    ADD CONSTRAINT metrics_pkey PRIMARY KEY (metricid);


--
-- TOC entry 2330 (class 2606 OID 19529)
-- Name: notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notificationid);


--
-- TOC entry 2348 (class 2606 OID 19659)
-- Name: ports_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY ports
    ADD CONSTRAINT ports_pkey PRIMARY KEY (portid);


--
-- TOC entry 2296 (class 2606 OID 19364)
-- Name: projects_envid_id_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_envid_id_key UNIQUE (envid, id);


--
-- TOC entry 2298 (class 2606 OID 19362)
-- Name: projects_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (projectid);


--
-- TOC entry 2247 (class 2606 OID 19111)
-- Name: roles_name_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- TOC entry 2249 (class 2606 OID 19109)
-- Name: roles_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (roleid);


--
-- TOC entry 2320 (class 2606 OID 19491)
-- Name: sites_envid_id_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY sites
    ADD CONSTRAINT sites_envid_id_key UNIQUE (envid, id);


--
-- TOC entry 2322 (class 2606 OID 19493)
-- Name: sites_luid_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY sites
    ADD CONSTRAINT sites_luid_key UNIQUE (luid);


--
-- TOC entry 2324 (class 2606 OID 19489)
-- Name: sites_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY sites
    ADD CONSTRAINT sites_pkey PRIMARY KEY (siteid, envid);


--
-- TOC entry 2251 (class 2606 OID 19148)
-- Name: state_control_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY state_control
    ADD CONSTRAINT state_control_pkey PRIMARY KEY (stateid);


--
-- TOC entry 2253 (class 2606 OID 19150)
-- Name: state_control_state_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY state_control
    ADD CONSTRAINT state_control_state_key UNIQUE (state);


--
-- TOC entry 2267 (class 2606 OID 19221)
-- Name: system_key_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY system
    ADD CONSTRAINT system_key_key UNIQUE (key);


--
-- TOC entry 2269 (class 2606 OID 19219)
-- Name: system_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY system
    ADD CONSTRAINT system_pkey PRIMARY KEY (envid, key);


--
-- TOC entry 2336 (class 2606 OID 19572)
-- Name: tableau_processes_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY tableau_processes
    ADD CONSTRAINT tableau_processes_pkey PRIMARY KEY (tid, agentid);


--
-- TOC entry 2271 (class 2606 OID 19240)
-- Name: users_name_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- TOC entry 2273 (class 2606 OID 19238)
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (userid);


--
-- TOC entry 2275 (class 2606 OID 19242)
-- Name: users_system_user_id_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_system_user_id_key UNIQUE (system_user_id);


--
-- TOC entry 2366 (class 2606 OID 113456)
-- Name: workbook_extracts_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY workbook_extracts
    ADD CONSTRAINT workbook_extracts_pkey PRIMARY KEY (sid);


--
-- TOC entry 2340 (class 2606 OID 19604)
-- Name: workbook_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY workbook_updates
    ADD CONSTRAINT workbook_updates_pkey PRIMARY KEY (wuid);


--
-- TOC entry 2342 (class 2606 OID 19606)
-- Name: workbook_updates_workbookid_revision_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY workbook_updates
    ADD CONSTRAINT workbook_updates_workbookid_revision_key UNIQUE (workbookid, revision);


--
-- TOC entry 2309 (class 2606 OID 19435)
-- Name: workbooks_envid_site_id_project_id_luid_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY workbooks
    ADD CONSTRAINT workbooks_envid_site_id_project_id_luid_key UNIQUE (envid, site_id, project_id, luid);


--
-- TOC entry 2311 (class 2606 OID 19433)
-- Name: workbooks_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY workbooks
    ADD CONSTRAINT workbooks_pkey PRIMARY KEY (workbookid);


--
-- TOC entry 2255 (class 2606 OID 19163)
-- Name: xid_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY xid
    ADD CONSTRAINT xid_pkey PRIMARY KEY (xid);


--
-- TOC entry 2277 (class 2606 OID 19267)
-- Name: yml_envid_key_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY yml
    ADD CONSTRAINT yml_envid_key_key UNIQUE (envid, key);


--
-- TOC entry 2279 (class 2606 OID 19265)
-- Name: yml_pkey; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY yml
    ADD CONSTRAINT yml_pkey PRIMARY KEY (ymlid, envid);


--
-- TOC entry 2281 (class 2606 OID 19269)
-- Name: yml_ymlid_key; Type: CONSTRAINT; Schema: public; Owner: palette; Tablespace: 
--

ALTER TABLE ONLY yml
    ADD CONSTRAINT yml_ymlid_key UNIQUE (ymlid);


--
-- TOC entry 2299 (class 1259 OID 19389)
-- Name: events_envid_event_type_timestamp_idx; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE INDEX events_envid_event_type_timestamp_idx ON events USING btree (envid, event_type, "timestamp");


--
-- TOC entry 2300 (class 1259 OID 19390)
-- Name: events_envid_level_timestamp_idx; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE INDEX events_envid_level_timestamp_idx ON events USING btree (envid, level, "timestamp");


--
-- TOC entry 2301 (class 1259 OID 19388)
-- Name: events_envid_timestamp_idx; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE INDEX events_envid_timestamp_idx ON events USING btree (envid, "timestamp");


--
-- TOC entry 2314 (class 1259 OID 19460)
-- Name: ix_agent_uuid; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE UNIQUE INDEX ix_agent_uuid ON agent USING btree (uuid);


--
-- TOC entry 2290 (class 1259 OID 19331)
-- Name: ix_cloud_name; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE INDEX ix_cloud_name ON cloud USING btree (name);


--
-- TOC entry 2258 (class 1259 OID 19177)
-- Name: ix_domain_name; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE UNIQUE INDEX ix_domain_name ON domain USING btree (name);


--
-- TOC entry 2265 (class 1259 OID 19209)
-- Name: ix_environment_name; Type: INDEX; Schema: public; Owner: palette; Tablespace: 
--

CREATE UNIQUE INDEX ix_environment_name ON environment USING btree (name);


--
-- TOC entry 2382 (class 2606 OID 19455)
-- Name: agent_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY agent
    ADD CONSTRAINT agent_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2390 (class 2606 OID 19589)
-- Name: agent_volumes_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY agent_volumes
    ADD CONSTRAINT agent_volumes_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2375 (class 2606 OID 19326)
-- Name: cloud_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY cloud
    ADD CONSTRAINT cloud_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2376 (class 2606 OID 19347)
-- Name: credentials_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY credentials
    ADD CONSTRAINT credentials_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2383 (class 2606 OID 19474)
-- Name: data_connections_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY data_connections
    ADD CONSTRAINT data_connections_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2405 (class 2606 OID 113482)
-- Name: datasource_extracts_extractid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_extracts
    ADD CONSTRAINT datasource_extracts_extractid_fkey FOREIGN KEY (extractid) REFERENCES extracts(extractid) ON DELETE CASCADE;


--
-- TOC entry 2407 (class 2606 OID 113492)
-- Name: datasource_extracts_fileid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_extracts
    ADD CONSTRAINT datasource_extracts_fileid_fkey FOREIGN KEY (fileid) REFERENCES files(fileid) ON DELETE CASCADE;


--
-- TOC entry 2406 (class 2606 OID 113487)
-- Name: datasource_extracts_parentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_extracts
    ADD CONSTRAINT datasource_extracts_parentid_fkey FOREIGN KEY (parentid) REFERENCES datasources(dsid) ON DELETE CASCADE;


--
-- TOC entry 2399 (class 2606 OID 113150)
-- Name: datasource_updates_dsid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_updates
    ADD CONSTRAINT datasource_updates_dsid_fkey FOREIGN KEY (dsid) REFERENCES datasources(dsid) ON DELETE CASCADE;


--
-- TOC entry 2400 (class 2606 OID 113309)
-- Name: datasource_updates_fileid_tds_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_updates
    ADD CONSTRAINT datasource_updates_fileid_tds_fkey FOREIGN KEY (fileid_tds) REFERENCES files(fileid) ON DELETE CASCADE;


--
-- TOC entry 2401 (class 2606 OID 113314)
-- Name: datasource_updates_fileid_tdsx_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasource_updates
    ADD CONSTRAINT datasource_updates_fileid_tdsx_fkey FOREIGN KEY (fileid_tdsx) REFERENCES files(fileid) ON DELETE CASCADE;


--
-- TOC entry 2398 (class 2606 OID 113132)
-- Name: datasources_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY datasources
    ADD CONSTRAINT datasources_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2380 (class 2606 OID 19418)
-- Name: email_sent_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY email_sent
    ADD CONSTRAINT email_sent_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2369 (class 2606 OID 19204)
-- Name: environment_domainid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY environment
    ADD CONSTRAINT environment_domainid_fkey FOREIGN KEY (domainid) REFERENCES domain(domainid) ON UPDATE CASCADE;


--
-- TOC entry 2378 (class 2606 OID 19383)
-- Name: events_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY events
    ADD CONSTRAINT events_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2374 (class 2606 OID 19306)
-- Name: extracts_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY extracts
    ADD CONSTRAINT extracts_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2379 (class 2606 OID 19404)
-- Name: files_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2395 (class 2606 OID 19642)
-- Name: firewall_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY firewall
    ADD CONSTRAINT firewall_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2385 (class 2606 OID 19512)
-- Name: http_requests_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY http_requests
    ADD CONSTRAINT http_requests_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2388 (class 2606 OID 19555)
-- Name: license_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY license
    ADD CONSTRAINT license_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2394 (class 2606 OID 19626)
-- Name: metrics_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY metrics
    ADD CONSTRAINT metrics_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2387 (class 2606 OID 19535)
-- Name: notifications_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2386 (class 2606 OID 19530)
-- Name: notifications_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2397 (class 2606 OID 19665)
-- Name: ports_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY ports
    ADD CONSTRAINT ports_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2396 (class 2606 OID 19660)
-- Name: ports_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY ports
    ADD CONSTRAINT ports_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2377 (class 2606 OID 19365)
-- Name: projects_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2384 (class 2606 OID 19494)
-- Name: sites_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY sites
    ADD CONSTRAINT sites_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2370 (class 2606 OID 19222)
-- Name: system_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY system
    ADD CONSTRAINT system_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2389 (class 2606 OID 19573)
-- Name: tableau_processes_agentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY tableau_processes
    ADD CONSTRAINT tableau_processes_agentid_fkey FOREIGN KEY (agentid) REFERENCES agent(agentid) ON DELETE CASCADE;


--
-- TOC entry 2371 (class 2606 OID 19243)
-- Name: users_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2372 (class 2606 OID 19248)
-- Name: users_roleid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_roleid_fkey FOREIGN KEY (roleid) REFERENCES roles(roleid);


--
-- TOC entry 2402 (class 2606 OID 113457)
-- Name: workbook_extracts_extractid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_extracts
    ADD CONSTRAINT workbook_extracts_extractid_fkey FOREIGN KEY (extractid) REFERENCES extracts(extractid) ON DELETE CASCADE;


--
-- TOC entry 2404 (class 2606 OID 113467)
-- Name: workbook_extracts_fileid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_extracts
    ADD CONSTRAINT workbook_extracts_fileid_fkey FOREIGN KEY (fileid) REFERENCES files(fileid) ON DELETE CASCADE;


--
-- TOC entry 2403 (class 2606 OID 113462)
-- Name: workbook_extracts_parentid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_extracts
    ADD CONSTRAINT workbook_extracts_parentid_fkey FOREIGN KEY (parentid) REFERENCES workbooks(workbookid) ON DELETE CASCADE;


--
-- TOC entry 2392 (class 2606 OID 113255)
-- Name: workbook_updates_fileid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_updates
    ADD CONSTRAINT workbook_updates_fileid_fkey FOREIGN KEY (fileid) REFERENCES files(fileid) ON DELETE CASCADE;


--
-- TOC entry 2393 (class 2606 OID 113304)
-- Name: workbook_updates_fileid_twbx_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_updates
    ADD CONSTRAINT workbook_updates_fileid_twbx_fkey FOREIGN KEY (fileid_twbx) REFERENCES files(fileid) ON DELETE CASCADE;


--
-- TOC entry 2391 (class 2606 OID 113066)
-- Name: workbook_updates_workbookid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbook_updates
    ADD CONSTRAINT workbook_updates_workbookid_fkey FOREIGN KEY (workbookid) REFERENCES workbooks(workbookid) ON DELETE CASCADE;


--
-- TOC entry 2381 (class 2606 OID 19436)
-- Name: workbooks_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY workbooks
    ADD CONSTRAINT workbooks_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2373 (class 2606 OID 19270)
-- Name: yml_envid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: palette
--

ALTER TABLE ONLY yml
    ADD CONSTRAINT yml_envid_fkey FOREIGN KEY (envid) REFERENCES environment(envid);


--
-- TOC entry 2520 (class 0 OID 0)
-- Dependencies: 5
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2016-07-04 08:38:42 CEST

--
-- PostgreSQL database dump complete
--

